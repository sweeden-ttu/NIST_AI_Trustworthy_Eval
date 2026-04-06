"""FastMCP server for rd-agent-mcp."""

import asyncio
import json
import uuid
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from rd_agent_mcp.config import Config
from rd_agent_mcp.lm_studio.client import LMStudioClient
from rd_agent_mcp.vectorstore.chroma import ChromaStore
from rd_agent_mcp.vectorstore.embeddings import SyncLMStudioEmbeddings
from rd_agent_mcp.tools.test_cases import TestCaseGenerator
from rd_agent_mcp.tools.research import ResearchTools
from rd_agent_mcp.agent_pipeline import execute_agent_pipeline
from rd_agent_mcp.research_runner import execute_research_phase
from rd_agent_mcp.tools import latex_section_critique as latex_critique


mcp = FastMCP("rd-agent-mcp")

_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create configuration."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


@mcp.tool()
async def health_check() -> dict:
    """Check system health."""
    client = LMStudioClient()
    try:
        lm_available = await client.is_available()
    except Exception:
        lm_available = False

    try:
        chroma = ChromaStore(
            persist_directory="./chroma_data",
            collection_name="research",
        )
        chroma_count = chroma.count()
    except Exception:
        chroma_count = 0

    return {
        "status": "healthy" if lm_available else "degraded",
        "lm_studio": "available" if lm_available else "unavailable",
        "embeddings_stored": chroma_count,
        "version": "0.1.0",
    }


@mcp.tool()
async def research_phase(
    topic: str,
    papers: list[str] = None,
    homework_pdf: str = None,
    topics: list[str] = None,
) -> dict:
    """Run full research pipeline for a topic."""
    return await execute_research_phase(
        topic=topic,
        papers=papers,
        homework_pdf=homework_pdf,
        topics=topics,
    )


@mcp.tool()
async def extract_questions(
    homework_pdf: str = None,
    papers: list[str] = None,
    topics: list[str] = None,
) -> list[dict]:
    """Extract questions from homework and papers."""
    from rd_agent_mcp.graph.nodes import extract_questions

    if papers is None:
        papers = []
    if topics is None:
        topics = []

    state = {
        "messages": [],
        "papers": papers,
        "topics": topics,
        "homework_pdf": homework_pdf,
        "questions": [],
        "experiments": [],
        "embeddings": {},
        "prompts": {},
        "agent_results": [],
        "results_json": None,
        "latex_sections": {},
        "schemas": {},
        "current_phase": "start",
        "run_id": str(uuid.uuid4()),
        "errors": [],
    }

    result = await extract_questions(state)
    return [q.model_dump() for q in result.get("questions", [])]


@mcp.tool()
async def design_experiments(
    questions: list[dict],
    related_work: list[str] = None,
) -> list[dict]:
    """Design experiments for questions."""
    from rd_agent_mcp.graph.nodes import design_experiments
    from rd_agent_mcp.graph.state import Question

    if related_work is None:
        related_work = []

    state = {
        "messages": [],
        "papers": related_work,
        "topics": [],
        "homework_pdf": None,
        "questions": [Question(**q) for q in questions],
        "experiments": [],
        "embeddings": {},
        "prompts": {},
        "agent_results": [],
        "results_json": None,
        "latex_sections": {},
        "schemas": {},
        "current_phase": "questions",
        "run_id": str(uuid.uuid4()),
        "errors": [],
    }

    result = await design_experiments(state)
    return [e.model_dump() for e in result.get("experiments", [])]


@mcp.tool()
async def create_embeddings(
    documents: list[str],
    metadata: list[dict] = None,
    model: str = "text-embedding-nomic-embed-text-v1.5",
) -> dict:
    """Generate and store embeddings in ChromaDB."""
    if metadata is None:
        metadata = []

    chroma = ChromaStore(
        persist_directory="./chroma_data",
        collection_name="research",
        embedding_function=SyncLMStudioEmbeddings(),
    )

    embeddings = {}
    for i, doc in enumerate(documents):
        doc_id = f"doc_{i}_{uuid.uuid4().hex[:8]}"
        meta = metadata[i] if i < len(metadata) else {}
        meta["source"] = "manual"

        chroma.add_text(
            text=doc,
            doc_id=doc_id,
            metadata=meta,
        )
        embeddings[doc_id] = doc

    return {"stored": len(embeddings), "ids": list(embeddings.keys())}


@mcp.tool()
async def search_embeddings(
    query: str,
    phase: str = None,
    question_id: str = None,
    top_k: int = 5,
) -> list[dict]:
    """Search stored embeddings by similarity."""
    chroma = ChromaStore(
        persist_directory="./chroma_data",
        collection_name="research",
        embedding_function=SyncLMStudioEmbeddings(),
    )

    filter_dict = {}
    if phase:
        filter_dict["phase"] = phase
    if question_id:
        filter_dict["question_id"] = question_id

    results = chroma.search(query=query, k=top_k, filter_dict=filter_dict or None)
    return results


@mcp.tool()
async def run_agent_pipeline(
    prompt: str,
    agent_type: str,
    language: str = "python",
    output_dir: str = "./output",
) -> dict:
    """Run agent pipeline with specified agent.

    ``agent_type`` must match a routed config, or use aliases: ``RagV1``/``rag`` → ``rd-agent``;
    ``ralph`` → ``adk-ralph``. The response includes ``agent_results_item``: pass ``[agent_results_item]``
    to ``compile_results``.
    """
    return await execute_agent_pipeline(
        prompt=prompt,
        agent_type=agent_type,
        language=language,
        output_dir=output_dir,
    )


@mcp.tool()
async def answer_question(
    question_id: str,
    sub_question: str,
    context: dict,
) -> dict:
    """Answer specific homework question."""
    tools = ResearchTools()
    return await tools.answer_question(
        question=sub_question,
        context=context,
    )


@mcp.tool()
async def generate_test_cases(
    question_id: str,
    experiment: dict,
    output_dir: str = "./test_cases",
) -> dict:
    """Generate test cases in YAML format."""
    generator = TestCaseGenerator(output_dir=output_dir)

    # Create test case
    from rd_agent_mcp.tools.test_cases import TestCaseConfig

    config = TestCaseConfig(**experiment)

    test_path = generator.create_test_case(
        question_id=question_id,
        test_id=experiment.get("test_id", f"{question_id}_test"),
        config=config,
    )

    # Create schema file
    schema = experiment.get("schema", {})
    schema_path = None
    if schema:
        schema_path = generator.create_schema_file(
            question_id=question_id,
            schema=schema,
        )

    return {
        "test_file": str(test_path),
        "schema_file": str(schema_path) if schema_path else None,
    }


@mcp.tool()
async def latex_section_critique_list_sections(
    project_root: str,
    latex_glob: str | None = None,
) -> dict:
    """List LaTeX section JSON files under project_root and their keys; optional critique paths."""
    glo = latex_glob or latex_critique.DEFAULT_LATEX_GLOB
    return await asyncio.to_thread(latex_critique.list_latex_sections, project_root, glo)


@mcp.tool()
async def latex_section_critique_index_ground_truth(
    project_root: str,
    collection_name: str | None = None,
    chunk_chars: int = 1600,
    force_reindex: bool = False,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    chroma_persist_directory: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict:
    """Chunk and embed q1/q2/q3 into Chroma; returns chunks_written and chunks_skipped."""
    cfg = get_config()
    kwargs: dict[str, Any] = {
        "project_root": project_root,
        "chunk_chars": chunk_chars,
        "force_reindex": force_reindex,
        "q1_path": q1_path,
        "q2_path": q2_path,
        "q3_path": q3_path,
        "collection_name": collection_name or latex_critique.DEFAULT_CRITIQUE_COLLECTION,
        "chroma_persist_directory": chroma_persist_directory,
        "embedding_model": embedding_model or cfg.embedding_model,
        "embedding_base_url": embedding_base_url or cfg.base_url,
    }
    return await asyncio.to_thread(latex_critique.index_ground_truth, **kwargs)


@mcp.tool()
async def latex_section_critique_retrieve_ground_truth(
    project_root: str,
    section_key: str,
    latex_fragment: str,
    collection_name: str | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    numeric_hint_json: dict | str | None = None,
    chroma_persist_directory: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict:
    """Retrieve ranked ground-truth chunks per q1/q2/q3 (no LLM)."""
    cfg = get_config()
    return await asyncio.to_thread(
        latex_critique.retrieve_ground_truth,
        project_root,
        section_key=section_key,
        latex_fragment=latex_fragment,
        numeric_hint_json=numeric_hint_json,
        top_k=top_k,
        per_source_k=per_source_k,
        collection_name=collection_name or latex_critique.DEFAULT_CRITIQUE_COLLECTION,
        chroma_persist_directory=chroma_persist_directory,
        embedding_model=embedding_model or cfg.embedding_model,
        embedding_base_url=embedding_base_url or cfg.base_url,
    )


@mcp.tool()
async def latex_section_critique_get_bundle(
    project_root: str,
    latex_relative_path: str,
    section_key: str,
    ground_truth_mode: str = "truncate",
    critique_path: str | None = None,
    numeric_path: str | None = None,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    max_q1_chars: int = 14000,
    max_q2_chars: int = 6000,
    max_q3_chars: int = 8000,
    collection_name: str | None = None,
    chroma_persist_directory: str | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict:
    """One section + numeric/critique slices + ground truth (truncate or hybrid RAG)."""
    if ground_truth_mode not in ("truncate", "rag"):
        raise ValueError('ground_truth_mode must be "truncate" or "rag"')
    cfg = get_config()
    return await asyncio.to_thread(
        latex_critique.get_section_bundle,
        project_root,
        latex_relative_path,
        section_key,
        critique_path=critique_path,
        numeric_path=numeric_path,
        q1_path=q1_path,
        q2_path=q2_path,
        q3_path=q3_path,
        max_q1_chars=max_q1_chars,
        max_q2_chars=max_q2_chars,
        max_q3_chars=max_q3_chars,
        ground_truth_mode=ground_truth_mode,  # type: ignore[arg-type]
        collection_name=collection_name or latex_critique.DEFAULT_CRITIQUE_COLLECTION,
        chroma_persist_directory=chroma_persist_directory,
        top_k=top_k,
        per_source_k=per_source_k,
        embedding_model=embedding_model or cfg.embedding_model,
        embedding_base_url=embedding_base_url or cfg.base_url,
    )


def _resolve_task_text(
    project_root: str,
    task_text: str | None,
    agent_yaml_path: str | None,
) -> str:
    if task_text:
        return task_text
    if not agent_yaml_path:
        raise ValueError("Provide task_text or agent_yaml_path")
    p = latex_critique.resolve_under_root(project_root, agent_yaml_path)
    return latex_critique.task_from_agent_yaml(p)


@mcp.tool()
async def latex_section_critique_build_prompt(
    project_root: str,
    latex_relative_path: str,
    section_key: str,
    task_text: str | None = None,
    agent_yaml_path: str | None = None,
    ground_truth_mode: str = "truncate",
    critique_path: str | None = None,
    numeric_path: str | None = None,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    max_q1_chars: int = 14000,
    max_q2_chars: int = 6000,
    max_q3_chars: int = 8000,
    collection_name: str | None = None,
    chroma_persist_directory: str | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict:
    """Build user_message for one-section critique (dry run)."""
    if ground_truth_mode not in ("truncate", "rag"):
        raise ValueError('ground_truth_mode must be "truncate" or "rag"')
    cfg = get_config()

    def _build() -> dict[str, Any]:
        task = _resolve_task_text(project_root, task_text, agent_yaml_path)
        bundle = latex_critique.get_section_bundle(
            project_root,
            latex_relative_path,
            section_key,
            critique_path=critique_path,
            numeric_path=numeric_path,
            q1_path=q1_path,
            q2_path=q2_path,
            q3_path=q3_path,
            max_q1_chars=max_q1_chars,
            max_q2_chars=max_q2_chars,
            max_q3_chars=max_q3_chars,
            ground_truth_mode=ground_truth_mode,  # type: ignore[arg-type]
            collection_name=collection_name or latex_critique.DEFAULT_CRITIQUE_COLLECTION,
            chroma_persist_directory=chroma_persist_directory,
            top_k=top_k,
            per_source_k=per_source_k,
            embedding_model=embedding_model or cfg.embedding_model,
            embedding_base_url=embedding_base_url or cfg.base_url,
        )
        user = latex_critique.build_section_critique_user_message(task, bundle)
        return {
            "user_message": user,
            "approx_bytes": len(user.encode("utf-8")),
        }

    return await asyncio.to_thread(_build)


@mcp.tool()
async def latex_section_critique_run_section_review(
    project_root: str,
    latex_relative_path: str,
    section_key: str,
    task_text: str | None = None,
    agent_yaml_path: str | None = None,
    ground_truth_mode: str = "truncate",
    critique_path: str | None = None,
    numeric_path: str | None = None,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    max_q1_chars: int = 14000,
    max_q2_chars: int = 6000,
    max_q3_chars: int = 8000,
    collection_name: str | None = None,
    chroma_persist_directory: str | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
    temperature: float = 0.2,
    timeout: float = 600.0,
    model: str | None = None,
    base_url: str | None = None,
) -> dict:
    """Run LM Studio chat for a single section; returns parsed JSON (section critique object)."""
    if ground_truth_mode not in ("truncate", "rag"):
        raise ValueError('ground_truth_mode must be "truncate" or "rag"')
    cfg = get_config()
    prompt_payload = await latex_section_critique_build_prompt(
        project_root=project_root,
        latex_relative_path=latex_relative_path,
        section_key=section_key,
        task_text=task_text,
        agent_yaml_path=agent_yaml_path,
        ground_truth_mode=ground_truth_mode,
        critique_path=critique_path,
        numeric_path=numeric_path,
        q1_path=q1_path,
        q2_path=q2_path,
        q3_path=q3_path,
        max_q1_chars=max_q1_chars,
        max_q2_chars=max_q2_chars,
        max_q3_chars=max_q3_chars,
        collection_name=collection_name,
        chroma_persist_directory=chroma_persist_directory,
        top_k=top_k,
        per_source_k=per_source_k,
        embedding_model=embedding_model,
        embedding_base_url=embedding_base_url,
    )
    user = prompt_payload["user_message"]
    m = model or cfg.chat_model
    bu = base_url or cfg.base_url
    client = LMStudioClient(
        model=m,
        base_url=bu,
        api_key=cfg.api_key,
        timeout=timeout,
    )
    try:
        raw = await client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous technical reviewer. Respond with one valid JSON object only; "
                        "no markdown code fences. For a single-section review, return exactly this shape: "
                        '{"grades":{"letter":"B","numeric":85},"claims":[],"consistency_notes":"","action_items":[]}'
                    ),
                },
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    finally:
        await client.close()
    parsed = latex_critique.parse_critique_json_response(raw)
    if isinstance(parsed, dict) and "grades" not in parsed and "section" in parsed:
        parsed = parsed["section"]
    return {"section_critique": parsed, "raw_model_text": raw}


@mcp.tool()
async def latex_section_critique_merge_partial(
    project_root: str,
    latex_relative_path: str,
    section_key: str,
    partial_section_critique: dict,
    critique_json_path: str | None = None,
    base_critique: dict | None = None,
    write_path: str | None = None,
) -> dict:
    """Merge one section into latex-sections-critique.json shape; optional write under project_root."""
    rel_crit = critique_json_path or latex_critique.DEFAULT_CRITIQUE_REL

    def _merge() -> dict[str, Any]:
        if base_critique is not None:
            base = json.loads(json.dumps(base_critique))
        else:
            p = latex_critique.resolve_under_root(project_root, rel_crit)
            if not p.is_file():
                base = {
                    "critique_version": 1,
                    "inputs": [],
                    "ground_truth_paths": [],
                    "sections_by_file": {},
                    "cross_cutting": {},
                }
            else:
                base = json.loads(p.read_text(encoding="utf-8"))
        merged = latex_critique.merge_section_into_critique(
            base, latex_relative_path, section_key, partial_section_critique
        )
        if write_path:
            out = latex_critique.resolve_under_root(project_root, write_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
        return merged

    return await asyncio.to_thread(_merge)


@mcp.tool()
async def latex_section_critique_run_cross_cutting(
    project_root: str,
    latex_relative_path: str,
    task_text: str | None = None,
    agent_yaml_path: str | None = None,
    critique_json_path: str | None = None,
    base_critique: dict | None = None,
    write_path: str | None = None,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    max_digest_chars: int = 4000,
    temperature: float = 0.2,
    timeout: float = 600.0,
    model: str | None = None,
    base_url: str | None = None,
) -> dict:
    """LM call to fill only cross_cutting using abstract/results/discussion/conclusion excerpts."""
    cfg = get_config()

    def _prep() -> tuple[str, dict[str, Any]]:
        task = _resolve_task_text(project_root, task_text, agent_yaml_path)
        subset = latex_critique.load_latex_subset_for_cross_cutting(
            project_root, latex_relative_path
        )
        gt = latex_critique.load_ground_truth_texts(
            project_root, q1_path=q1_path, q2_path=q2_path, q3_path=q3_path
        )
        user = latex_critique.build_cross_cutting_user_message(
            task, latex_relative_path, subset, gt, max_chars=max_digest_chars
        )
        rel_crit = critique_json_path or latex_critique.DEFAULT_CRITIQUE_REL
        if base_critique is not None:
            base = json.loads(json.dumps(base_critique))
        else:
            p = latex_critique.resolve_under_root(project_root, rel_crit)
            base = (
                json.loads(p.read_text(encoding="utf-8"))
                if p.is_file()
                else {
                    "critique_version": 1,
                    "inputs": [],
                    "ground_truth_paths": [],
                    "sections_by_file": {},
                    "cross_cutting": {},
                }
            )
        return user, base

    user, base = await asyncio.to_thread(_prep)
    client = LMStudioClient(
        model=model or cfg.chat_model,
        base_url=base_url or cfg.base_url,
        api_key=cfg.api_key,
        timeout=timeout,
    )
    try:
        raw = await client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous technical reviewer. Respond with one valid JSON object only; "
                        'no markdown code fences. Shape: {"cross_cutting":{"results_vs_discussion":"...",'
                        '"results_vs_conclusion":"...","abstract_vs_body":"..."}}'
                    ),
                },
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    finally:
        await client.close()
    parsed = latex_critique.parse_critique_json_response(raw)
    cc = parsed.get("cross_cutting") if isinstance(parsed, dict) else None
    if not isinstance(cc, dict):
        raise ValueError(f"Model did not return cross_cutting dict: {parsed!r}")
    out = dict(base)
    out["cross_cutting"] = cc
    if write_path:
        outp = latex_critique.resolve_under_root(project_root, write_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return {"critique": out, "raw_model_text": raw}


@mcp.tool()
async def compile_results(
    agent_results: list[dict],
    output_format: str = "json",
) -> str:
    """Compile agent results into final output."""
    from rd_agent_mcp.graph.nodes import compile_results
    from rd_agent_mcp.graph.state import AgentResultModel

    state = {
        "messages": [],
        "papers": [],
        "topics": [],
        "homework_pdf": None,
        "questions": [],
        "experiments": [],
        "embeddings": {},
        "prompts": {},
        "agent_results": [AgentResultModel(**r) for r in agent_results],
        "results_json": None,
        "latex_sections": {},
        "schemas": {},
        "current_phase": "agent",
        "run_id": str(uuid.uuid4()),
        "errors": [],
    }

    result = await compile_results(state)

    if output_format == "json":
        return result.get("results_json", "{}")
    else:
        return json.dumps(result.get("latex_sections", {}), indent=2)


@mcp.tool()
async def list_phases() -> list[dict]:
    """List available research phases."""
    return [
        {
            "id": "questions",
            "name": "Questions",
            "description": "Extract questions from homework and papers",
            "inputs": ["papers", "topics", "homework_pdf"],
            "outputs": ["questions"],
        },
        {
            "id": "experiment",
            "name": "Experiment Design",
            "description": "Design experiments for questions",
            "inputs": ["questions"],
            "outputs": ["experiments", "prompts"],
        },
        {
            "id": "embeddings",
            "name": "Embeddings",
            "description": "Generate embeddings for documents",
            "inputs": ["papers", "topics"],
            "outputs": ["embeddings"],
        },
        {
            "id": "agent",
            "name": "Agent Execution",
            "description": "Run agents with intelligent routing",
            "inputs": ["prompts", "experiments"],
            "outputs": ["agent_results"],
            "parallel": True,
        },
        {
            "id": "results",
            "name": "Results Compilation",
            "description": "Compile results into JSON and LaTeX",
            "inputs": ["agent_results"],
            "outputs": ["results_json", "latex_sections"],
        },
    ]
