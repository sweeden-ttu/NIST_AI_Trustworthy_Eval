"""Smoke tests: imports and agent graph helpers."""

import asyncio
import os

import pytest

from rd_agent_mcp.agents.coordinator import Coordinator
from rd_agent_mcp.config import Config
from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL


def test_coordinator_import_and_instantiate() -> None:
    c = Coordinator(rd_agent_path="/tmp/does-not-exist-rd", adk_ralph_path="/tmp/does-not-exist-adk")
    assert c.router is not None


def test_config_default_agent_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)
    c = Config.from_env()
    assert "rd-agent" in c.agents.rd_agent_path
    assert "adk-ralph" in c.agents.adk_ralph_path
    assert c.base_url == DEFAULT_LM_STUDIO_BASE_URL
    assert "192.168.0.13" in DEFAULT_LM_STUDIO_BASE_URL


def test_run_agents_simulated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RD_AGENT_MCP_EXEC_AGENTS", "false")

    from rd_agent_mcp.graph.nodes import run_agents
    from rd_agent_mcp.graph.state import Experiment

    state = {
        "experiments": [
            Experiment(
                question_id="q1",
                test_cases=[{"id": "t1"}],
            )
        ],
        "prompts": {},
    }
    out = asyncio.run(run_agents(state))  # type: ignore[arg-type]
    assert out["current_phase"] == "agent"
    assert len(out["agent_results"]) >= 1
