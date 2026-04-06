"""Questions phase implementation."""

from rd_agent_mcp.phases.base import BasePhase


class QuestionsPhase(BasePhase):
    """Phase 0: Extract questions from homework and papers."""

    def __init__(self):
        super().__init__("questions")
        self._extract_questions = None
        self._generate_embeddings = None

    async def run(self, state):
        """Run questions extraction and embeddings generation."""
        from rd_agent_mcp.graph.nodes import extract_questions, generate_embeddings

        # First extract questions
        state = await extract_questions(state)

        # Then generate embeddings for related work
        if state.get("papers") or state.get("topics"):
            state = await generate_embeddings(state)

        return state

    def validate_input(self, state):
        """Validate input has papers or topics."""
        papers = state.get("papers", [])
        topics = state.get("topics", [])
        homework = state.get("homework_pdf")
        return bool(papers or topics or homework)
