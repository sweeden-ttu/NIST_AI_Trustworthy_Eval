"""Results phase implementation."""

from rd_agent_mcp.phases.base import BasePhase


class ResultsPhase(BasePhase):
    """Phase 4: Compile results into JSON and LaTeX."""

    def __init__(self):
        super().__init__("results")

    async def run(self, state):
        """Run results compilation."""
        from rd_agent_mcp.graph.nodes import compile_results

        return await compile_results(state)

    def validate_input(self, state):
        """Validate input has agent results."""
        results = state.get("agent_results", [])
        return len(results) > 0
