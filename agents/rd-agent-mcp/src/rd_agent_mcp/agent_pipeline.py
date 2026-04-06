"""Shared agent pipeline logic (MCP tool + Python API)."""

from __future__ import annotations

import uuid
from typing import Any

from rd_agent_mcp.agents.adk_ralph import ADKRalphWrapper
from rd_agent_mcp.agents.rd_agent import RDAgentWrapper
from rd_agent_mcp.agents.router import AgentRouter


def normalize_agent_type(agent_type: str) -> str:
    """Map aliases (e.g. RagV1) to supported agents: rd-agent | adk-ralph."""
    raw = (agent_type or "").strip()
    key = raw.lower().replace(" ", "").replace("_", "-")
    aliases = {
        "ragv1": "rd-agent",
        "rag-v1": "rd-agent",
        "rag": "rd-agent",
        "rdagent": "rd-agent",
        "microsoftrdagent": "rd-agent",
        "ralph": "adk-ralph",
        "adkralph": "adk-ralph",
    }
    if key in aliases:
        return aliases[key]
    if raw in ("rd-agent", "adk-ralph"):
        return raw
    return raw


def agent_result_for_compile(
    *,
    agent_id: str,
    agent_type: str,
    success: bool,
    output: str | dict | None,
    artifacts: list | None,
    error: str | None,
) -> dict[str, Any]:
    """Shape expected by compile_results / AgentResultModel."""
    if isinstance(output, str):
        out_dict: dict = {"text": output}
    elif isinstance(output, dict):
        out_dict = output
    else:
        out_dict = {}
    return {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "output": out_dict,
        "artifacts": list(artifacts or []),
        "status": "completed" if success else "failed",
        "error": error,
    }


async def execute_agent_pipeline(
    prompt: str,
    agent_type: str,
    language: str = "python",
    output_dir: str = "./output",
) -> dict[str, Any]:
    """Run rd-agent or adk-ralph; same behavior as MCP ``run_agent_pipeline``."""
    normalized = normalize_agent_type(agent_type)
    if normalized not in ("rd-agent", "adk-ralph"):
        router = AgentRouter()
        planned = [c.agent_type for c in router.route(prompt, {"language": language})]
        return {
            "success": False,
            "error": (
                f"Unknown agent_type {agent_type!r}. "
                f"Use rd-agent, adk-ralph, or aliases RagV1/rag → rd-agent, ralph → adk-ralph. "
                f"Router would prefer: {planned}"
            ),
        }

    aid = f"{normalized}-{uuid.uuid4().hex[:8]}"
    if normalized == "rd-agent":
        agent = RDAgentWrapper()
        result = await agent.run(prompt)
        item = agent_result_for_compile(
            agent_id=aid,
            agent_type="rd-agent",
            success=result.success,
            output=result.output,
            artifacts=result.artifacts,
            error=result.error,
        )
        return {
            "success": result.success,
            "output": result.output,
            "artifacts": result.artifacts,
            "error": result.error,
            "agent_results_item": item,
        }

    agent = ADKRalphWrapper()
    result = await agent.run_pipeline(prompt, language=language)
    item = agent_result_for_compile(
        agent_id=aid,
        agent_type="adk-ralph",
        success=result.success,
        output=result.output,
        artifacts=result.artifacts,
        error=result.error,
    )
    return {
        "success": result.success,
        "output": result.output,
        "artifacts": result.artifacts,
        "error": result.error,
        "agent_results_item": item,
    }
