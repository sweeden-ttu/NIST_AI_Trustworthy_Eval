# Research graph (rd-agent-mcp)

Source: `rd_agent_mcp/graph/research_graph.py`

## Phase order

1. **extract_questions** — Consumes `homework_pdf` path, `papers`, `topics`. Uses `load_homework_excerpt()` for PDF sidecar `.txt` or `pypdf`.
2. **generate_embeddings** — Chroma + LM Studio embeddings for paper/topic strings.
3. **design_experiments** — Per-question experiment YAML fragments via LLM.
4. **design_prompts** — rd-agent vs adk-ralph prompt skeletons per experiment.
5. **run_agents** — If `RD_AGENT_MCP_EXEC_AGENTS=true`, runs [`Coordinator`](../../rd-agent-mcp/src/rd_agent_mcp/agents/coordinator.py) with `RD_AGENT_PATH` / `ADK_RALPH_PATH`; else simulated stubs.
6. **compile_results** — JSON + IEEE-oriented LaTeX section stubs in state.

## Router

[`AgentRouter`](../../rd-agent-mcp/src/rd_agent_mcp/agents/router.py) classifies tasks (data analysis, code generation, etc.) and returns ordered `AgentConfig` entries.
