"""Test case generator for rd-agent-mcp."""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class TestCaseConfig(BaseModel):
    """Configuration for a test case."""

    class_name: str
    alg: str
    depth: int
    diagram: Optional[str] = None
    num_agents: int = 2
    phase: str = "experiment"
    start_state: Optional[str] = None
    win_states: list[str] = Field(default_factory=list)
    lose_states: list[str] = Field(default_factory=list)
    successors: dict = Field(default_factory=dict)
    evaluation: dict = Field(default_factory=dict)
    criteria: list[str] = Field(default_factory=list)
    expected_output: Optional[dict] = None
    test_config: Optional[dict] = None
    agent_configs: Optional[list[dict]] = None


class AgentDefinition(BaseModel):
    """Agent definition for test case."""

    name: str
    type: str  # rd-agent or adk-ralph
    model: str
    provider: str = "lm_studio"
    command: dict
    environment: dict = Field(default_factory=dict)
    tools: list[dict] = Field(default_factory=list)
    retry: dict = Field(default_factory={"max_attempts": 3, "backoff": "exponential"})
    timeout: int = 600
    chroma: Optional[dict] = None


class TestCaseGenerator:
    """Generator for research test cases in YAML format."""

    def __init__(self, output_dir: str = "./test_cases"):
        self.output_dir = Path(output_dir)

    def create_test_case(
        self,
        question_id: str,
        test_id: str,
        config: TestCaseConfig,
        output_path: Optional[str] = None,
    ) -> Path:
        """Create a test case YAML file."""
        if output_path is None:
            q_dir = self.output_dir / question_id
            q_dir.mkdir(parents=True, exist_ok=True)
            output_path = q_dir / f"{test_id}.yaml"

        data = config.model_dump(exclude_none=True)

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return Path(output_path)

    def create_agent_definition(
        self,
        agent_type: str,
        question_id: str,
        config: AgentDefinition,
        output_path: Optional[str] = None,
    ) -> Path:
        """Create an agent definition YAML file."""
        if output_path is None:
            agents_dir = self.output_dir / question_id / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            output_path = agents_dir / f"{agent_type}-{question_id}.yaml"

        data = config.model_dump(exclude_none=True)

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return Path(output_path)

    def create_schema_file(
        self,
        question_id: str,
        schema: dict,
        output_path: Optional[str] = None,
    ) -> Path:
        """Create a schema file for expected outputs."""
        if output_path is None:
            schemas_dir = self.output_dir / question_id / "schemas"
            schemas_dir.mkdir(parents=True, exist_ok=True)
            output_path = schemas_dir / "schema.json"

        import json

        with open(output_path, "w") as f:
            json.dump(schema, f, indent=2)

        return Path(output_path)

    def create_config(self, order: list[str], output_path: Optional[str] = None) -> Path:
        """Create the main CONFIG file."""
        if output_path is None:
            output_path = self.output_dir / "CONFIG"

        config = {
            "order": order,
            "metadata": {
                "course": "C S 4383/5388-001",
                "semester": "Spring 2026",
                "assignment": "Homework 1",
            },
        }

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return Path(output_path)

    def create_question_config(
        self,
        question_id: str,
        max_points: int = 15,
        passing_threshold: float = 0.7,
        output_path: Optional[str] = None,
    ) -> Path:
        """Create a question-specific CONFIG file."""
        if output_path is None:
            q_dir = self.output_dir / question_id
            q_dir.mkdir(parents=True, exist_ok=True)
            output_path = q_dir / "CONFIG"

        config = {
            "max_points": max_points,
            "class": f"Research{question_id.title()}Question",
            "passing_threshold": passing_threshold,
        }

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return Path(output_path)

    def generate_rd_agent_test(
        self,
        question_id: str,
        task: str,
        scenario: str = "data_science",
    ) -> tuple[Path, Path]:
        """Generate test case and agent definition for rd-agent."""
        # Create test case
        test_config = TestCaseConfig(
            class_name="ResearchRDAgentTest",
            alg="RDAgent",
            depth=1,
            phase="agent",
            criteria=[
                "Code generates successfully",
                "Tests pass",
                "Results match expected schema",
            ],
        )
        test_path = self.create_test_case(question_id, f"rd-agent-{question_id}", test_config)

        # Create agent definition
        agent_config = AgentDefinition(
            name=f"rd-agent-{question_id}",
            type="rd-agent",
            model="ibm/granite-4-h-tiny",
            provider="lm_studio",
            command={
                "module": "rdagent",
                "scenario": scenario,
                "args": ["--task", task],
            },
            tools=[
                {"name": "file_write", "output": f"output/{question_id}/results.json"},
                {"name": "test_execution"},
            ],
        )
        agent_path = self.create_agent_definition("rd-agent", question_id, agent_config)

        return test_path, agent_path

    def generate_adk_ralph_test(
        self,
        question_id: str,
        task: str,
        language: str = "python",
    ) -> tuple[Path, Path]:
        """Generate test case and agent definition for adk-ralph."""
        # Create test case
        test_config = TestCaseConfig(
            class_name="ResearchADKRalphTest",
            alg="ADKRalph",
            depth=1,
            phase="agent",
            criteria=[
                "PRD generated",
                "Design created",
                "Code compiles",
                "Tests pass",
            ],
        )
        test_path = self.create_test_case(question_id, f"adk-ralph-{question_id}", test_config)

        # Create agent definition
        agent_config = AgentDefinition(
            name=f"adk-ralph-{question_id}",
            type="adk-ralph",
            model="granite4:3b",
            provider="ollama",
            command={
                "binary": "cargo",
                "args": ["run", "--", task],
            },
            tools=[
                {"name": "generate_prd", "output": "prd.md"},
                {"name": "generate_design", "output": "design.md"},
                {"name": "generate_code", "language": language},
            ],
        )
        agent_path = self.create_agent_definition("adk-ralph", question_id, agent_config)

        return test_path, agent_path
