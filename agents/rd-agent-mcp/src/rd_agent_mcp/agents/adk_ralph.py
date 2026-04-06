"""ADK-Ralph wrapper for rd-agent-mcp."""

import os
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class ADKRalphResult(BaseModel):
    """Result from adk-ralph execution."""

    success: bool
    output: str
    error: Optional[str] = None
    artifacts: list[str] = []
    prd_file: Optional[str] = None
    design_file: Optional[str] = None
    tasks_file: Optional[str] = None


class ADKRalphWrapper:
    """Wrapper for adk-ralph."""

    def __init__(self, repo_path: str = "./agents/adk-ralph"):
        self.repo_path = Path(repo_path)
        self.default_timeout = 900

    async def run_pipeline(
        self,
        prompt: str,
        language: str = "python",
        timeout: int = None,
        environment: dict = None,
    ) -> ADKRalphResult:
        """Run adk-ralph pipeline."""
        if timeout is None:
            timeout = self.default_timeout

        env = {
            "OLLAMA_HOST": "http://localhost:11434",
            "RALPH_MODEL_PROVIDER": "ollama",
            "RALPH_LOCAL_MODEL": "granite4:3b",
            "RUSTC_WRAPPER": "sccache",
            **os.environ.copy(),
        }
        if environment:
            env.update(environment)

        try:
            result = await asyncio.create_subprocess_exec(
                "cargo",
                "run",
                "--",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path),
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                result.kill()
                return ADKRalphResult(
                    success=False,
                    output="",
                    error=f"Timeout after {timeout} seconds",
                )

            output = stdout.decode("utf-8", errors="replace")
            artifacts = self._find_artifacts(output)

            if result.returncode == 0:
                return ADKRalphResult(
                    success=True,
                    output=output,
                    artifacts=artifacts,
                    prd_file=artifacts[0] if "prd.md" in artifacts else None,
                    design_file=artifacts[0] if "design.md" in artifacts else None,
                    tasks_file=artifacts[0] if "tasks.json" in artifacts else None,
                )
            else:
                return ADKRalphResult(
                    success=False,
                    output=output,
                    error=stderr.decode("utf-8", errors="replace"),
                )

        except Exception as e:
            return ADKRalphResult(
                success=False,
                output="",
                error=str(e),
            )

    async def run_chat(self, message: str, timeout: int = 300) -> ADKRalphResult:
        """Run adk-ralph in chat mode."""
        env = {
            "OLLAMA_HOST": "http://localhost:11434",
            "RALPH_MODEL_PROVIDER": "ollama",
        }

        try:
            result = await asyncio.create_subprocess_exec(
                "cargo",
                "run",
                "--",
                "chat",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path),
                env=env,
                stdin=asyncio.subprocess.PIPE,
            )

            # Send message and wait for response
            stdout, stderr = await asyncio.wait_for(
                result.communicate(input=f"{message}\n/exit\n".encode()),
                timeout=timeout,
            )

            return ADKRalphResult(
                success=result.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace") if stderr else None,
            )

        except Exception as e:
            return ADKRalphResult(
                success=False,
                output="",
                error=str(e),
            )

    async def run_code_generation(
        self,
        language: str,
        requirements: str,
        output_dir: str = "./output",
    ) -> ADKRalphResult:
        """Generate code in specified language."""
        prompt = f"Create a {language} project: {requirements}"
        return await self.run_pipeline(prompt, language=language)

    def _find_artifacts(self, output: str) -> list[str]:
        """Find artifact paths in output."""
        import re

        artifacts = []
        patterns = [
            r"prd\.md",
            r"design\.md",
            r"tasks\.json",
            r"progress\.json",
            r"bin/[/\w-]+",
            r"src/[/\w-]+\.\w+",
            r"output[/\w-]+\.\w+",
        ]
        for pattern in patterns:
            artifacts.extend(re.findall(pattern, output))
        return list(set(artifacts))

    def is_available(self) -> bool:
        """Check if adk-ralph is available."""
        try:
            result = subprocess.run(
                ["cargo", "check"],
                capture_output=True,
                timeout=30,
                cwd=str(self.repo_path),
            )
            return result.returncode == 0
        except Exception:
            return False
