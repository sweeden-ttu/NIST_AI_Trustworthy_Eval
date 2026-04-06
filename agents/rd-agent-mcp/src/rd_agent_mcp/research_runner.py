"""Full LangGraph research pipeline (shared by MCP tool and Python API)."""

from __future__ import annotations

import uuid
from typing import Any

from rd_agent_mcp.graph.research_graph import ResearchGraph


async def execute_research_phase(
    topic: str,
    papers: list[str] | None = None,
    homework_pdf: str | None = None,
    topics: list[str] | None = None,
) -> dict[str, Any]:
    """Run extract_questions → embeddings → design → prompts → agents → compile."""
    if papers is None:
        papers = []
    if topics is None:
        topics = [topic]

    graph = ResearchGraph()
    initial_state = {
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

    try:
        result = await graph.run(initial_state)
        return {
            "success": True,
            "run_id": result.get("run_id"),
            "questions": len(result.get("questions", [])),
            "experiments": len(result.get("experiments", [])),
            "agent_results": len(result.get("agent_results", [])),
            "results_json": result.get("results_json"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
