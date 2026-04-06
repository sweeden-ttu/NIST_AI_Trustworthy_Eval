"""RDAgent wrapper for rd-agent-mcp."""

import os
import subprocess

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL
import json
import asyncio
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class RDAgentResult(BaseModel):
    """Result from rd-agent execution."""

    success: bool
    output: str
    error: Optional[str] = None
    artifacts: list[str] = []
    metrics: dict = {}


class RDAgentWrapper:
    """Wrapper for rd-agent."""

    def __init__(self, repo_path: str = "./agents/rd-agent"):
        self.repo_path = Path(repo_path)
        self.default_timeout = 600

    async def run(
        self,
        task: str,
        scenario: str = "data_science",
        timeout: int = None,
        environment: dict = None,
    ) -> RDAgentResult:
        """Run rd-agent for a task."""
        if timeout is None:
            timeout = self.default_timeout

        env = os.environ.copy()
        lm_base = env.get("LM_STUDIO_BASE_URL") or DEFAULT_LM_STUDIO_BASE_URL
        env["LM_STUDIO_BASE_URL"] = lm_base
        env.setdefault("LITELLM_OPENAI_API_BASE", lm_base)
        env.setdefault("OPENAI_API_BASE", lm_base)
        env.setdefault("LITELLM_OPENAI_API_KEY", "lm-studio")
        if environment:
            env.update(environment)

        try:
            result = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "rdagent",
                scenario,
                "--task",
                task,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path),
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                result.kill()
                return RDAgentResult(
                    success=False,
                    output="",
                    error=f"Timeout after {timeout} seconds",
                )

            if result.returncode == 0:
                return RDAgentResult(
                    success=True,
                    output=stdout.decode("utf-8", errors="replace"),
                    artifacts=self._find_artifacts(stdout.decode()),
                )
            else:
                return RDAgentResult(
                    success=False,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace"),
                )

        except Exception as e:
            return RDAgentResult(
                success=False,
                output="",
                error=str(e),
            )

    def _find_artifacts(self, output: str) -> list[str]:
        """Find artifact paths in output."""
        import re

        artifacts = []
        # Look for common artifact patterns
        patterns = [
            r"output[/\w-]+\.\w+",
            r"results[/\w-]+\.\w+",
            r"figures?[/\w-]+\.\w+",
        ]
        for pattern in patterns:
            artifacts.extend(re.findall(pattern, output))
        return list(set(artifacts))

    async def run_research(
        self,
        papers: list[str],
        topics: list[str],
        output_dir: str = "./output",
    ) -> RDAgentResult:
        """Run research on papers."""
        task = f"Analyze papers {papers} for topics {topics}"
        return await self.run(task, scenario="general_model")

    async def run_data_analysis(
        self,
        dataset: str,
        analysis_type: str,
        output_dir: str = "./output",
    ) -> RDAgentResult:
        """Run data analysis."""
        task = f"Analyze {dataset} with {analysis_type}"
        return await self.run(task, scenario="data_science")

    def is_available(self) -> bool:
        """Check if rd-agent is available."""
        try:
            result = subprocess.run(
                ["python", "-m", "rdagent", "--help"],
                capture_output=True,
                timeout=10,
                cwd=str(self.repo_path),
            )
            return result.returncode == 0
        except Exception:
            return False
