"""Embeddings phase implementation."""

from rd_agent_mcp.phases.base import BasePhase


class EmbeddingsPhase(BasePhase):
    """Phase 2: Generate embeddings for documents."""

    def __init__(self):
        super().__init__("embeddings")

    async def run(self, state):
        """Run embedding generation."""
        from rd_agent_mcp.graph.nodes import generate_embeddings

        return await generate_embeddings(state)

    def validate_input(self, state):
        """Validate input has papers or topics."""
        papers = state.get("papers", [])
        topics = state.get("topics", [])
        return bool(papers or topics)
