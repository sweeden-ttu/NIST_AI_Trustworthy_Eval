# Knowledge base

## Course extracts (Docling)

Markdown derived from instructor materials lives under [`course/`](./course/). Regenerate from the repo root:

```bash
uv sync --extra kb
uv run --extra kb python scripts/extract_course_kb_docling.py
```

Sources:

- `scripts/course/AI Agent Evaluation.pdf`
- `scripts/course/AgentEval-H-1.pptx`

## OpenCode judge / instructor

Canonical prompts and model hints for the **NIST experiment loop** and the **OpenCode MCP judge** are under [`opencode/`](./opencode/). Point OpenCode’s project `directory` at this repository root so paths resolve.

## NIST experiment orchestration

- Full graph loop (LangGraph): `uv run --extra graph python scripts/nist_experiment_graph_loop.py --help`
- Full graph + KB extract: `uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py --extract-kb`
