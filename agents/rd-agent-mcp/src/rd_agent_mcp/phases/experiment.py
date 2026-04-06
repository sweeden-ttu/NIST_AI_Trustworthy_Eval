"""Experiment phase implementation."""

from rd_agent_mcp.phases.base import BasePhase


class ExperimentPhase(BasePhase):
    """Phase 1: Design experiments for questions."""

    def __init__(self):
        super().__init__("experiment")

    async def run(self, state):
        """Run experiment design."""
        from rd_agent_mcp.graph.nodes import design_experiments, design_prompts

        # Design experiments
        state = await design_experiments(state)

        # Generate prompts for agents
        if state.get("experiments"):
            state = await design_prompts(state)

        return state

    def validate_input(self, state):
        """Validate input has questions."""
        questions = state.get("questions", [])
        return len(questions) > 0
