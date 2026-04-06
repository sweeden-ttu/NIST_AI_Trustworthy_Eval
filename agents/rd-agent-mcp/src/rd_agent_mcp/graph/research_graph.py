"""Main LangGraph research workflow."""

from langgraph.graph import StateGraph, END, START

from rd_agent_mcp.graph.state import ResearchState
from rd_agent_mcp.graph.nodes import (
    extract_questions,
    generate_embeddings,
    design_experiments,
    design_prompts,
    run_agents,
    compile_results,
)
from rd_agent_mcp.graph.edges import (
    should_run_parallel,
    should_continue,
)


def create_research_graph():
    """Create the main research workflow graph."""

    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("extract_questions", extract_questions)
    graph.add_node("generate_embeddings", generate_embeddings)
    graph.add_node("design_experiments", design_experiments)
    graph.add_node("design_prompts", design_prompts)
    graph.add_node("run_agents", run_agents)
    graph.add_node("compile_results", compile_results)

    # Define entry point
    graph.set_entry_point("extract_questions")

    # Add edges
    graph.add_edge("extract_questions", "generate_embeddings")
    graph.add_edge("generate_embeddings", "design_experiments")
    graph.add_edge("design_experiments", "design_prompts")
    graph.add_edge("design_prompts", "run_agents")
    graph.add_edge("run_agents", "compile_results")
    graph.add_edge("compile_results", END)

    return graph.compile()


class ResearchGraph:
    """Wrapper for the research workflow graph."""

    def __init__(self):
        self.graph = create_research_graph()

    async def run(self, initial_state: dict) -> dict:
        """Run the research workflow."""
        return await self.graph.ainvoke(initial_state)

    def run_sync(self, initial_state: dict) -> dict:
        """Run the research workflow synchronously."""
        import asyncio

        return asyncio.run(self.run(initial_state))
