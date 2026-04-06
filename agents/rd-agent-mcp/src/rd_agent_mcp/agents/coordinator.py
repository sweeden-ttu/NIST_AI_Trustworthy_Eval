"""Multi-agent coordinator for rd-agent-mcp."""

import asyncio
from typing import Optional

from pydantic import BaseModel

from rd_agent_mcp.agents.router import AgentRouter
from rd_agent_mcp.agents.rd_agent import RDAgentWrapper, RDAgentResult
from rd_agent_mcp.agents.adk_ralph import ADKRalphWrapper, ADKRalphResult


class CoordinatorResult(BaseModel):
    """Result from coordinator."""

    success: bool
    rd_agent_result: Optional[RDAgentResult] = None
    adk_ralph_result: Optional[ADKRalphResult] = None
    combined_artifacts: list[str] = []
    errors: list[str] = []


class Coordinator:
    """Coordinates multiple agents for research tasks."""

    def __init__(
        self,
        rd_agent_path: str = "./agents/rd-agent",
        adk_ralph_path: str = "./agents/adk-ralph",
    ):
        self.router = AgentRouter()
        self.rd_agent = RDAgentWrapper(repo_path=rd_agent_path)
        self.adk_ralph = ADKRalphWrapper(repo_path=adk_ralph_path)

    async def run_task(self, task: str, context: dict | None = None) -> CoordinatorResult:
        """Run a task with intelligent agent routing."""
        if context is None:
            context = {}

        agent_configs = self.router.route(task, context)
        rd_result = None
        adk_result = None
        errors: list[str] = []

        rd_configs = [c for c in agent_configs if c.agent_type == "rd-agent"]
        adk_configs = [c for c in agent_configs if c.agent_type == "adk-ralph"]

        if rd_configs:
            try:
                config = rd_configs[0]
                rd_result = await self.rd_agent.run(
                    task=task,
                    environment=config.environment,
                    timeout=config.timeout,
                )
            except Exception as e:
                errors.append(f"rd-agent error: {str(e)}")

        if adk_configs:
            try:
                config = adk_configs[0]
                adk_result = await self.adk_ralph.run_pipeline(
                    prompt=task,
                    environment=config.environment,
                    timeout=config.timeout,
                )
            except Exception as e:
                errors.append(f"adk-ralph error: {str(e)}")

        artifacts: list[str] = []
        if rd_result and rd_result.artifacts:
            artifacts.extend(rd_result.artifacts)
        if adk_result and adk_result.artifacts:
            artifacts.extend(adk_result.artifacts)

        success = bool((rd_result and rd_result.success) or (adk_result and adk_result.success))

        return CoordinatorResult(
            success=success,
            rd_agent_result=rd_result,
            adk_ralph_result=adk_result,
            combined_artifacts=artifacts,
            errors=errors,
        )

    async def run_parallel(
        self, tasks: list[str], context: dict | None = None
    ) -> list[CoordinatorResult | BaseException]:
        """Run multiple tasks in parallel."""
        if context is None:
            context = {}

        coroutines = [self.run_task(task, context) for task in tasks]
        return await asyncio.gather(*coroutines, return_exceptions=True)

    async def run_sequential(
        self, tasks: list[str], context: dict | None = None
    ) -> list[CoordinatorResult]:
        """Run multiple tasks sequentially."""
        if context is None:
            context = {}

        results: list[CoordinatorResult] = []
        for task in tasks:
            result = await self.run_task(task, context)
            results.append(result)
            if result.combined_artifacts:
                context["previous_artifacts"] = result.combined_artifacts
        return results
