# DesignPatterns → rd-agent-mcp phases

Sources: a local checkout of the **DesignPatterns** repo (pattern markdown files and optional Python planners) and the **rd-agent-mcp** package.

| Design pattern doc | MCP phase / component |
|--------------------|------------------------|
| Tool use / MCP (`10-Model-Context-Protocol.md`, `05-Tool-Use.md`) | MCP server tools in `rd_agent_mcp/server.py`; agent subprocess tools |
| Planning / decomposition | `design_experiments`, `design_prompts` nodes |
| Evaluation & monitoring (`19-Evaluation-and-Monitoring.md`) | `test_cases` YAML `evaluation` / `criteria`; future `test_runner` |
| Parallelization (`03-Parallelization.md`) | `Coordinator.run_parallel` (optional batch tasks) |
| Reflection (`04-Reflection.md`) | Manual loop: re-run `run_phase` with updated `topics` / papers |

Use iterative coding agents (`iterative_value_coding_agent.py`, `GranitePlanningAgent.py`) as **reference** for state-machine YAML in `test_cases`, not as runtime dependencies of the template.
