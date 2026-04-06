"""Agent phase implementation."""

from rd_agent_mcp.phases.base import BasePhase


class AgentPhase(BasePhase):
    """Phase 3: Run agents with intelligent routing."""

    def __init__(self):
        super().__init__("agent")

    async def run(self, state):
        """Run agents with intelligent routing."""
        from rd_agent_mcp.graph.nodes import run_agents

        return await run_agents(state)

    def validate_input(self, state):
        """Validate input has prompts or experiments."""
        prompts = state.get("prompts", {})
        experiments = state.get("experiments", [])
        return bool(prompts or experiments)
