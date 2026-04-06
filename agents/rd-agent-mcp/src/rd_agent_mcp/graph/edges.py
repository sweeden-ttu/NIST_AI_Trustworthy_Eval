"""Conditional edges for research workflow."""

from typing import Literal
from rd_agent_mcp.graph.state import ResearchState


def should_run_parallel(state: ResearchState) -> Literal["parallel", "sequential"]:
    """Determine if agents should run in parallel or sequential."""
    experiments = state.get("experiments", [])
    if len(experiments) > 1:
        return "parallel"
    return "sequential"


def should_continue(state: ResearchState) -> Literal["continue", "end"]:
    """Determine if workflow should continue."""
    errors = state.get("errors", [])
    if errors and len(errors) > 3:
        return "end"
    return "continue"


def route_to_agent(state: ResearchState) -> Literal["run_rd_agent", "run_adk_ralph"]:
    """Route to specific agent based on task."""
    # Simple routing based on current phase
    current_phase = state.get("current_phase", "")
    if "data" in current_phase or "analysis" in current_phase:
        return "run_rd_agent"
    return "run_adk_ralph"


def is_experiment_complete(state: ResearchState) -> bool:
    """Check if experiment is complete."""
    experiments = state.get("experiments", [])
    return len(experiments) > 0


def has_errors(state: ResearchState) -> bool:
    """Check if there are errors."""
    errors = state.get("errors", [])
    return len(errors) > 0
