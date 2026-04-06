"""Research tools for rd-agent-mcp."""

import json
import asyncio
from pathlib import Path
from typing import Optional
from rd_agent_mcp.lm_studio.client import LMStudioClient


class ResearchTools:
    """Tools for research tasks."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_hypothesis(
        self,
        related_work: str,
        experiment_setup: str,
        results_schema: str,
    ) -> dict:
        """Generate hypothesis based on related work and setup."""
        client = LMStudioClient()

        try:
            prompt = f"""Based on the following related work and experiment setup,
            generate a research hypothesis.

            Related Work:
            {related_work}

            Experiment Setup:
            {experiment_setup}

            Expected Results Schema:
            {results_schema}

            Return a JSON object with:
            - hypothesis: The hypothesis statement
            - variables: List of independent and dependent variables
            - predictions: Expected outcomes
            - metrics: How success will be measured
            """

            response = await client.chat([{"role": "user", "content": prompt}])

            # Parse JSON response
            json_match = None
            import re

            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                json_match = match.group()

            if json_match:
                return json.loads(json_match)
            else:
                return {
                    "hypothesis": response,
                    "variables": [],
                    "predictions": [],
                    "metrics": [],
                }
        finally:
            await client.close()

    async def answer_question(
        self,
        question: str,
        context: dict,
    ) -> dict:
        """Answer a research question with evidence."""
        client = LMStudioClient()

        try:
            prompt = f"""Answer the following research question using the provided context.

            Question: {question}

            Context:
            {json.dumps(context, indent=2)}

            Return a JSON object with:
            - answer: The answer to the question
            - evidence: Supporting evidence from context
            - confidence: Confidence level (0-1)
            - sources: List of source references
            """

            response = await client.chat([{"role": "user", "content": prompt}])

            import re

            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                return json.loads(match.group())
            return {"answer": response, "evidence": [], "confidence": 0.5, "sources": []}
        finally:
            await client.close()

    def save_results(
        self,
        data: dict,
        filename: str,
        format: str = "json",
    ) -> Path:
        """Save research results to file."""
        output_path = self.output_dir / filename

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "yaml":
            import yaml

            with open(output_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
        elif format == "markdown":
            with open(output_path, "w") as f:
                f.write(self._dict_to_markdown(data))
        else:
            raise ValueError(f"Unknown format: {format}")

        return output_path

    def _dict_to_markdown(self, data: dict, level: int = 1) -> str:
        """Convert dictionary to markdown."""
        lines = []
        for key, value in data.items():
            heading = "#" * level
            lines.append(f"{heading} {key}\n")
            if isinstance(value, dict):
                lines.append(self._dict_to_markdown(value, level + 1))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._dict_to_markdown(item, level + 1))
                    else:
                        lines.append(f"- {item}\n")
            else:
                lines.append(f"{value}\n")
            lines.append("\n")
        return "".join(lines)

    async def generate_json_schema(
        self,
        description: str,
        expected_fields: list[str],
    ) -> dict:
        """Generate a JSON schema for experiment results."""
        client = LMStudioClient()

        try:
            prompt = f"""Generate a JSON Schema for the following experiment results.

            Description: {description}
            Expected Fields: {", ".join(expected_fields)}

            Return a complete JSON Schema in JSON format.
            """

            response = await client.chat([{"role": "user", "content": prompt}])

            import re

            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                return json.loads(match.group())
            return {"type": "object", "properties": {}}
        finally:
            await client.close()

    def create_experiment_summary(
        self,
        experiment_id: str,
        results: dict,
        artifacts: list[str],
    ) -> Path:
        """Create an experiment summary document."""
        summary = {
            "experiment_id": experiment_id,
            "results": results,
            "artifacts": artifacts,
            "status": "completed",
        }
        return self.save_results(summary, f"{experiment_id}_summary.json")
