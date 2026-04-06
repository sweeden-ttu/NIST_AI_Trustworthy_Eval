"""LangGraph state definitions for research workflow."""

from typing import TypedDict, Annotated, Optional
from typing import Literal
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class Question(BaseModel):
    """Research question model."""

    id: str
    text: str
    sub_questions: list["Question"] = Field(default_factory=list)
    related_work: list[str] = Field(default_factory=list)
    expected_outcome: str = "json"


class Experiment(BaseModel):
    """Experiment model."""

    question_id: str
    test_cases: list[dict] = Field(default_factory=list)
    configs: dict = Field(default_factory=dict)
    schema_file: Optional[str] = None


class AgentResultModel(BaseModel):
    """Agent execution result model."""

    agent_id: str
    agent_type: str  # "rd-agent" or "adk-ralph"
    output: dict = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    status: str = "pending"
    error: Optional[str] = None


class ResearchState(TypedDict):
    """Main state for research workflow."""

    # Messages (for LangGraph)
    messages: Annotated[list, add_messages]

    # Phase 0: Questions
    homework_pdf: Optional[str]
    papers: list[str]
    topics: list[str]
    questions: list[Question]

    # Phase 1: Experiments
    experiments: list[Experiment]

    # Phase 2: Embeddings
    embeddings: dict  # doc_id -> embedding_id in ChromaDB

    # Phase 3: Prompts
    prompts: dict  # question_id -> prompt

    # Phase 4: Agent Results
    agent_results: list[AgentResultModel]

    # Phase 5: Final Output
    results_json: Optional[str]
    latex_sections: dict

    # Schema for results
    schemas: dict  # question_id -> schema dict

    # Graph metadata
    current_phase: str
    run_id: str
    errors: list[str]


class PhaseInput(TypedDict):
    """Input for a specific phase."""

    homework_pdf: Optional[str]
    papers: list[str]
    topics: list[str]
    questions: Optional[list[Question]]
    experiments: Optional[list[Experiment]]
    run_id: str


class PhaseOutput(TypedDict):
    """Output from a specific phase."""

    questions: Optional[list[Question]]
    experiments: Optional[list[Experiment]]
    embeddings: Optional[dict]
    prompts: Optional[dict]
    agent_results: Optional[list[AgentResultModel]]
    results_json: Optional[str]
    latex_sections: Optional[dict]
    current_phase: str
    errors: list[str]


# Phase types
PhaseType = Literal["questions", "experiment", "embeddings", "agent", "results"]
AgentType = Literal["rd-agent", "adk-ralph", "both"]


class PhaseConfig(BaseModel):
    """Configuration for a research phase."""

    phase: PhaseType
    description: str
    primary_agent: AgentType
    parallel_subagents: bool = False
    subagent_configs: list[dict] = Field(default_factory=list)
