# MCP and agent examples (rd-ralph-template)

These snippets connect the homework PDF, [`test_cases/`](../test_cases), [`rd-agent-mcp`](https://github.com/sweeden-ttu/rd-agent-mcp), and submodules under [`agents/`](../agents).

## Prerequisites

- Python 3.11+ with `rd-agent-mcp` installed (`pip install -e /path/to/rd-agent-mcp`).
- Optional: LM Studio or cloud keys as configured in `rd-agent-mcp` [`Config`](../../rd-agent-mcp/src/rd_agent_mcp/config.py).
- Submodules: see [SUBMODULES.md](../SUBMODULES.md).

## Environment (template root)

```bash
export RD_AGENT_PATH="${RD_AGENT_PATH:-./agents/rd-agent}"
export ADK_RALPH_PATH="${ADK_RALPH_PATH:-./agents/adk-ralph}"
# Set to true only when you intend to spawn real agent processes:
export RD_AGENT_MCP_EXEC_AGENTS="${RD_AGENT_MCP_EXEC_AGENTS:-false}"
```

## Files

| File | Purpose |
|------|---------|
| [research-graph-overview.md](./research-graph-overview.md) | LangGraph phase order and state keys |
| [mcp-tool-payloads.json](./mcp-tool-payloads.json) | Example arguments for MCP tools |
| [agent-commands.sh](./agent-commands.sh) | rd-agent (Python) and adk-ralph (Rust) invocations |
| [designpatterns-to-phases.md](./designpatterns-to-phases.md) | Map DesignPatterns topics to MCP phases |
| [lm-studio-local.md](./lm-studio-local.md) | Default LAN LM Studio URL (`192.168.0.13:1234/v1`) and preset pointer |

Homework text for PDF extraction: keep `homework-assignment.txt` next to `homework-assignment.pdf`, or rely on optional `pypdf` in the **rd-agent-mcp** package (`rd_agent_mcp.utils.homework_text`).
