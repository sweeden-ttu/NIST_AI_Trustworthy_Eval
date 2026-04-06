"""LangGraph node implementations."""

import os
from typing import Optional

from rd_agent_mcp.config import Config
from rd_agent_mcp.lm_studio.client import LMStudioClient
from rd_agent_mcp.vectorstore.chroma import ChromaStore
from rd_agent_mcp.vectorstore.embeddings import SyncLMStudioEmbeddings
from rd_agent_mcp.graph.state import ResearchState, Question, Experiment, AgentResultModel
from rd_agent_mcp.agents.router import AgentRouter
from rd_agent_mcp.utils.homework_text import load_homework_excerpt


async def extract_questions(state: ResearchState) -> ResearchState:
    """Phase 0: Extract questions from homework PDF and papers."""
    cfg = Config.from_env()
    client = LMStudioClient(model=cfg.chat_model, base_url=cfg.base_url, api_key=cfg.api_key)

    try:
        hw_path = state.get("homework_pdf")
        homework_body = load_homework_excerpt(hw_path if isinstance(hw_path, str) else None)
        prompt = f"""Extract research questions from:
        - Homework (excerpt or path): {homework_body}
        - Papers: {state.get("papers", [])}
        - Topics: {state.get("topics", [])}

        Format the questions following this structure:
        - q1: [main question]
          - q1a: [sub question a]
          - q1b: [sub question b]
        - q2: [main question]
        etc.

        Return ONLY a JSON array of question objects with fields:
        - id: question identifier
        - text: question text
        - sub_questions: array of sub-question objects
        - related_work: array of related paper IDs
        - expected_outcome: expected output format
        """

        response = await client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant that extracts questions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        questions = _parse_questions(response)
        return {
            "questions": questions,
            "current_phase": "questions",
        }
    except Exception as e:
        return {
            "questions": [],
            "errors": [f"Questions extraction failed: {str(e)}"],
            "current_phase": "questions",
        }
    finally:
        await client.close()


def _parse_questions(text: str) -> list[Question]:
    """Parse questions from LLM response."""
    import json
    import re

    # Try to extract JSON from response
    json_match = re.search(r"\[.*\]", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return [Question(**q) for q in data]
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: parse manually
    questions = []
    lines = text.split("\n")
    current = None
    for line in lines:
        if line.strip().startswith("q") and ":" in line:
            parts = line.split(":", 1)
            q_id = parts[0].strip()
            q_text = parts[1].strip() if len(parts) > 1 else ""
            current = Question(id=q_id, text=q_text)
            questions.append(current)
    return questions


async def generate_embeddings(state: ResearchState) -> ResearchState:
    """Phase 2: Generate embeddings for related work."""
    chroma = ChromaStore(
        persist_directory="./chroma_data",
        collection_name="research",
        embedding_function=SyncLMStudioEmbeddings(),
    )

    embeddings = {}
    try:
        for i, paper in enumerate(state.get("papers", [])):
            doc_id = f"paper_{i}"
            # In real implementation, fetch paper content
            text = f"Research paper content for: {paper}"
            chroma.add_text(
                text=text,
                doc_id=doc_id,
                metadata={
                    "source": "paper",
                    "phase": "embeddings",
                    "paper_id": paper,
                },
            )
            embeddings[paper] = doc_id

        # Embed topics
        for i, topic in enumerate(state.get("topics", [])):
            doc_id = f"topic_{i}"
            chroma.add_text(
                text=topic,
                doc_id=doc_id,
                metadata={
                    "source": "topic",
                    "phase": "embeddings",
                },
            )
            embeddings[f"topic_{i}"] = doc_id

        return {
            "embeddings": embeddings,
            "current_phase": "embeddings",
        }
    except Exception as e:
        return {
            "embeddings": {},
            "errors": [f"Embedding generation failed: {str(e)}"],
            "current_phase": "embeddings",
        }


async def design_experiments(state: ResearchState) -> ResearchState:
    """Phase 1: Design experiments for each question."""
    cfg = Config.from_env()
    client = LMStudioClient(model=cfg.chat_model, base_url=cfg.base_url, api_key=cfg.api_key)

    experiments = []
    try:
        for question in state.get("questions", []):
            prompt = f"""Design experiments for the following research question:
            {question.text}

            Generate test cases in YAML format with:
            - test_id: unique identifier
            - question_id: {question.id}
            - criteria: evaluation criteria
            - expected_output: expected output format

            Return ONLY a YAML array of experiment objects.
            """

            response = await client.chat([{"role": "user", "content": prompt}])

            exp = Experiment(
                question_id=question.id,
                test_cases=[{"raw": response}],
                configs={"model": "ibm/granite-4-h-tiny"},
            )
            experiments.append(exp)

        return {
            "experiments": experiments,
            "current_phase": "experiment",
        }
    except Exception as e:
        return {
            "experiments": [],
            "errors": [f"Experiment design failed: {str(e)}"],
            "current_phase": "experiment",
        }
    finally:
        await client.close()


async def design_prompts(state: ResearchState) -> ResearchState:
    """Phase 2: Generate prompts for sub-agents."""
    prompts = {}
    for exp in state.get("experiments", []):
        prompt = f"""Generate prompts for the following experiment:
        Question ID: {exp.question_id}
        Test Cases: {len(exp.test_cases)} cases

        Create separate prompts for:
        1. rd-agent: For data analysis and research
        2. adk-ralph: For code generation and implementation

        Return JSON with:
        - rd_agent_prompt: prompt for rd-agent
        - adk_ralph_prompt: prompt for adk-ralph
        """
        prompts[exp.question_id] = prompt

    return {
        "prompts": prompts,
        "current_phase": "prompt",
    }


def _exec_agents_enabled() -> bool:
    return os.getenv("RD_AGENT_MCP_EXEC_AGENTS", "").lower() in ("1", "true", "yes")


async def run_agents(state: ResearchState) -> ResearchState:
    """Phase 3: Run agents with intelligent routing."""
    router = AgentRouter()
    results: list[AgentResultModel] = []

    exec_real = _exec_agents_enabled()

    if exec_real:
        from rd_agent_mcp.config import Config
        from rd_agent_mcp.agents.coordinator import Coordinator

        cfg = Config.from_env()
        coordinator = Coordinator(
            rd_agent_path=cfg.agents.rd_agent_path,
            adk_ralph_path=cfg.agents.adk_ralph_path,
        )

    for exp in state.get("experiments", []):
        task = f"{exp.question_id}: {exp.test_cases}"
        extra = state.get("prompts", {}).get(exp.question_id)
        if isinstance(extra, str):
            task = f"{task}\n\n{extra}"

        agent_configs = router.route(
            task=task,
            context={"experiments": state.get("experiments", [])},
        )

        if exec_real:
            coord_result = await coordinator.run_task(
                task,
                context={"experiments": state.get("experiments", [])},
            )
            if coord_result.rd_agent_result is not None:
                r = coord_result.rd_agent_result
                out = r.output[-4000:] if len(r.output) > 4000 else r.output
                results.append(
                    AgentResultModel(
                        agent_id=f"rd-agent-{exp.question_id}",
                        agent_type="rd-agent",
                        output={"status": "executed", "stdout_tail": out, "success": r.success},
                        artifacts=r.artifacts,
                        status="completed" if r.success else "failed",
                        error=r.error,
                    )
                )
            if coord_result.adk_ralph_result is not None:
                a = coord_result.adk_ralph_result
                out = a.output[-4000:] if len(a.output) > 4000 else a.output
                results.append(
                    AgentResultModel(
                        agent_id=f"adk-ralph-{exp.question_id}",
                        agent_type="adk-ralph",
                        output={"status": "executed", "stdout_tail": out, "success": a.success},
                        artifacts=a.artifacts,
                        status="completed" if a.success else "failed",
                        error=a.error,
                    )
                )
            if (
                coord_result.rd_agent_result is None
                and coord_result.adk_ralph_result is None
                and not coord_result.errors
            ):
                results.append(
                    AgentResultModel(
                        agent_id=f"none-{exp.question_id}",
                        agent_type="unknown",
                        output={"status": "no_agent_output"},
                        status="skipped",
                    )
                )
            for err in coord_result.errors:
                results.append(
                    AgentResultModel(
                        agent_id=f"coordinator-{exp.question_id}",
                        agent_type="coordinator",
                        output={"status": "error"},
                        status="failed",
                        error=err,
                    )
                )
            continue

        for config in agent_configs:
            if config.agent_type == "rd-agent":
                result = AgentResultModel(
                    agent_id=f"rd-agent-{exp.question_id}",
                    agent_type="rd-agent",
                    output={"status": "simulated", "config": config.model_dump()},
                    artifacts=[],
                    status="skipped",
                )
            elif config.agent_type == "adk-ralph":
                result = AgentResultModel(
                    agent_id=f"adk-ralph-{exp.question_id}",
                    agent_type="adk-ralph",
                    output={"status": "simulated", "config": config.model_dump()},
                    artifacts=[],
                    status="skipped",
                )
            else:
                result = AgentResultModel(
                    agent_id=f"unknown-{exp.question_id}",
                    agent_type="unknown",
                    output={"status": "skipped"},
                    status="skipped",
                )
            results.append(result)

    return {
        "agent_results": results,
        "current_phase": "agent",
    }


async def compile_results(state: ResearchState) -> ResearchState:
    """Phase 4: Compile results into JSON and LaTeX."""
    import json

    results = {
        "run_id": state.get("run_id", "unknown"),
        "questions": [q.model_dump() for q in state.get("questions", [])],
        "experiments": [e.model_dump() for e in state.get("experiments", [])],
        "agent_results": [r.model_dump() for r in state.get("agent_results", [])],
    }

    latex_sections = {
        "abstract": "\\begin{abstract}\\label{sec:abstract}\n% IEEE abstract text\n\\end{abstract}",
        "introduction": "\\section{Introduction}\\label{sec:intro}",
        "related_work": "\\section{Related Work}\\label{sec:related}",
        "methodology": "\\section{Methodology}\\label{sec:method}",
        "experiments": "\\section{Experimental Setup}\\label{sec:exp}",
        "results": "\\section{Results}\\label{sec:results}",
        "discussion": "\\section{Discussion}\\label{sec:disc}",
        "reproducibility": "\\section{Reproducibility}\\label{sec:repro}",
        "conclusion": "\\section{Conclusion}\\label{sec:conc}",
    }

    return {
        "results_json": json.dumps(results, indent=2),
        "latex_sections": latex_sections,
        "current_phase": "results",
    }
