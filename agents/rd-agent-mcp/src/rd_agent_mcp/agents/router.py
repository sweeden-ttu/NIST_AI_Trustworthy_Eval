"""Intelligent agent router for task distribution."""

import os
from typing import Literal

from pydantic import BaseModel

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL


class AgentConfig(BaseModel):
    """Configuration for an agent execution."""

    agent_type: Literal["rd-agent", "adk-ralph"]
    command: str
    args: list[str] = []
    environment: dict = {}
    timeout: int = 600
    priority: int = 0


TASK_PATTERNS = {
    "data_analysis": {
        "keywords": ["data", "analysis", "dataset", "csv", "metrics", "benchmark", "statistics"],
        "primary": "rd-agent",
        "secondary": "adk-ralph",
    },
    "literature_review": {
        "keywords": ["survey", "review", "papers", "related.work", "literature", "academic"],
        "primary": "rd-agent",
        "secondary": "adk-ralph",
    },
    "code_generation": {
        "keywords": ["implement", "generate", "create.*code", "build", "write.*code", "code"],
        "primary": "adk-ralph",
        "secondary": "rd-agent",
    },
    "experiment_design": {
        "keywords": ["design", "experiment", "hypothesis", "test.case", "setup"],
        "primary": "both",
        "secondary": None,
    },
    "results_compilation": {
        "keywords": ["compile", "json", "table", "figure", "latex", "document", "report"],
        "primary": "rd-agent",
        "secondary": "adk-ralph",
    },
    "visualization": {
        "keywords": ["plot", "chart", "graph", "diagram", "visual", "visualize"],
        "primary": "adk-ralph",
        "secondary": "rd-agent",
    },
}


class AgentRouter:
    """Router for intelligent agent selection based on task characteristics."""

    def __init__(self):
        self.patterns = TASK_PATTERNS

    def classify_task(self, task: str) -> str:
        """Classify a task based on keywords."""
        task_lower = task.lower()

        scores = {}
        for category, config in self.patterns.items():
            score = 0
            for keyword in config["keywords"]:
                import re

                if re.search(keyword, task_lower):
                    score += 1
            if score > 0:
                scores[category] = score

        if not scores:
            return "code_generation"  # Default to code generation

        return max(scores, key=scores.get)

    def route(self, task: str, context: dict = None) -> list[AgentConfig]:
        """Route a task to appropriate agent(s)."""
        if context is None:
            context = {}

        category = self.classify_task(task)
        config = self.patterns[category]

        agents = []

        # Primary agent
        if config["primary"] == "both":
            # Both agents for experiment design
            agents.append(self._create_rd_agent_config(task, context, priority=1))
            agents.append(self._create_adk_ralph_config(task, context, priority=1))
        elif config["primary"] == "rd-agent":
            agents.append(self._create_rd_agent_config(task, context, priority=1))
        elif config["primary"] == "adk-ralph":
            agents.append(self._create_adk_ralph_config(task, context, priority=1))

        # Secondary agent (if applicable)
        if config["secondary"] and config["secondary"] != config["primary"]:
            if config["secondary"] == "rd-agent":
                agents.append(self._create_rd_agent_config(task, context, priority=2))
            elif config["secondary"] == "adk-ralph":
                agents.append(self._create_adk_ralph_config(task, context, priority=2))

        # Sort by priority
        agents.sort(key=lambda x: x.priority)
        return agents

    def _create_rd_agent_config(self, task: str, context: dict, priority: int) -> AgentConfig:
        """Create rd-agent configuration."""
        lm_base = os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_LM_STUDIO_BASE_URL)
        return AgentConfig(
            agent_type="rd-agent",
            command="rdagent",
            args=["data_science", "--task", task],
            environment={
                "LM_STUDIO_BASE_URL": lm_base,
                "LITELLM_OPENAI_API_BASE": lm_base,
                "OPENAI_API_BASE": lm_base,
                "LITELLM_OPENAI_API_KEY": "lm-studio",
            },
            timeout=600,
            priority=priority,
        )

    def _create_adk_ralph_config(self, task: str, context: dict, priority: int) -> AgentConfig:
        """Create adk-ralph configuration."""
        return AgentConfig(
            agent_type="adk-ralph",
            command="cargo",
            args=["run", "--", task],
            environment={
                "OLLAMA_HOST": "http://localhost:11434",
                "RALPH_MODEL_PROVIDER": "ollama",
                "RALPH_LOCAL_MODEL": "granite4:3b",
            },
            timeout=900,
            priority=priority,
        )

    def get_agent_capabilities(self, agent_type: str) -> dict:
        """Get capabilities of an agent type."""
        capabilities = {
            "rd-agent": {
                "strengths": [
                    "Data analysis and processing",
                    "ML model training and evaluation",
                    "Literature review and synthesis",
                    "Benchmark execution",
                    "Research hypothesis generation",
                ],
                "languages": ["Python", "R", "SQL"],
                "output_formats": ["JSON", "CSV", "Python scripts"],
            },
            "adk-ralph": {
                "strengths": [
                    "Code generation and implementation",
                    "Multi-language support",
                    "Test-driven development",
                    "System architecture design",
                    "CLI tool creation",
                ],
                "languages": ["Rust", "Python", "TypeScript", "Go", "Java"],
                "output_formats": ["Binary", "Library", "CLI", "JSON"],
            },
        }
        return capabilities.get(agent_type, {})
