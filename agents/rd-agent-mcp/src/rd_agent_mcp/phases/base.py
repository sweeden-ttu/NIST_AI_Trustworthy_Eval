"""Research phases for rd-agent-mcp."""

from abc import ABC, abstractmethod
from typing import Optional
from rd_agent_mcp.graph.state import ResearchState


class BasePhase(ABC):
    """Abstract base class for research phases."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, state: ResearchState) -> ResearchState:
        """Run the phase."""
        pass

    @abstractmethod
    def validate_input(self, state: ResearchState) -> bool:
        """Validate input state for this phase."""
        pass

    def get_requirements(self) -> dict:
        """Get requirements for this phase."""
        return {"description": self.name}


class QuestionsPhase(BasePhase):
    """Phase 0: Extract questions from homework and papers."""

    def __init__(self):
        super().__init__("questions")

    async def run(self, state: ResearchState) -> ResearchState:
        """Run questions extraction."""
        from rd_agent_mcp.graph.nodes import extract_questions

        return await extract_questions(state)

    def validate_input(self, state: ResearchState) -> bool:
        """Validate input has papers or topics."""
        papers = state.get("papers", [])
        topics = state.get("topics", [])
        homework = state.get("homework_pdf")
        return bool(papers or topics or homework)

    def get_requirements(self) -> dict:
        return {
            "description": "Extract research questions from sources",
            "inputs": ["papers", "topics", "homework_pdf"],
            "outputs": ["questions"],
            "models": ["ibm/granite-4-h-tiny"],
        }


class ExperimentPhase(BasePhase):
    """Phase 1: Design experiments for questions."""

    def __init__(self):
        super().__init__("experiment")

    async def run(self, state: ResearchState) -> ResearchState:
        """Run experiment design."""
        from rd_agent_mcp.graph.nodes import design_experiments

        return await design_experiments(state)

    def validate_input(self, state: ResearchState) -> bool:
        """Validate input has questions."""
        questions = state.get("questions", [])
        return len(questions) > 0

    def get_requirements(self) -> dict:
        return {
            "description": "Design experiments for research questions",
            "inputs": ["questions"],
            "outputs": ["experiments"],
            "models": ["ibm/granite-4-h-tiny"],
        }


class EmbeddingsPhase(BasePhase):
    """Phase 2: Generate embeddings for documents."""

    def __init__(self):
        super().__init__("embeddings")

    async def run(self, state: ResearchState) -> ResearchState:
        """Run embedding generation."""
        from rd_agent_mcp.graph.nodes import generate_embeddings

        return await generate_embeddings(state)

    def validate_input(self, state: ResearchState) -> bool:
        """Validate input has papers or topics."""
        papers = state.get("papers", [])
        topics = state.get("topics", [])
        return bool(papers or topics)

    def get_requirements(self) -> dict:
        return {
            "description": "Generate embeddings for documents",
            "inputs": ["papers", "topics"],
            "outputs": ["embeddings"],
            "models": ["text-embedding-nomic-embed-text-v1.5"],
            "storage": "ChromaDB",
        }


class AgentPhase(BasePhase):
    """Phase 3: Run agents with intelligent routing."""

    def __init__(self):
        super().__init__("agent")

    async def run(self, state: ResearchState) -> ResearchState:
        """Run agents."""
        from rd_agent_mcp.graph.nodes import run_agents

        return await run_agents(state)

    def validate_input(self, state: ResearchState) -> bool:
        """Validate input has prompts."""
        prompts = state.get("prompts", {})
        experiments = state.get("experiments", [])
        return bool(prompts or experiments)

    def get_requirements(self) -> dict:
        return {
            "description": "Run agents with intelligent routing",
            "inputs": ["prompts", "experiments"],
            "outputs": ["agent_results"],
            "agents": ["rd-agent", "adk-ralph"],
            "parallel": True,
        }


class ResultsPhase(BasePhase):
    """Phase 4: Compile results into JSON and LaTeX."""

    def __init__(self):
        super().__init__("results")

    async def run(self, state: ResearchState) -> ResearchState:
        """Run results compilation."""
        from rd_agent_mcp.graph.nodes import compile_results

        return await compile_results(state)

    def validate_input(self, state: ResearchState) -> bool:
        """Validate input has agent results."""
        results = state.get("agent_results", [])
        return len(results) > 0

    def get_requirements(self) -> dict:
        return {
            "description": "Compile agent results into JSON and LaTeX",
            "inputs": ["agent_results"],
            "outputs": ["results_json", "latex_sections"],
        }
