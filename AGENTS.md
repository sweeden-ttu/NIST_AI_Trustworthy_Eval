# OpenCode / agent instructions (NIST trustworthy evaluation)

This repository’s active homework track is the **14-item NIST-style trustworthy AI questionnaire** (`scripts/nist_quiz_prompts.py`, `test_cases/rd_agent/q1`–`q14`).

## Judge and instructor role

When acting as **judge or instructor** via **OpenCode MCP**, follow:

1. [`knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md`](knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md)
2. [`knowledge_base/opencode/recommended_models.json`](knowledge_base/opencode/recommended_models.json) for default **Nemotron 3 Super Free** (OpenRouter) — verify IDs with `opencode_provider_models` if needed.
3. [`knowledge_base/opencode/OPENCODE_RUN_TEMPLATES.md`](knowledge_base/opencode/OPENCODE_RUN_TEMPLATES.md) for MCP call shapes.

Project model default for OpenCode CLI/TUI is set in [`opencode.json`](opencode.json). Override in user config if you use another provider.

## Course material (Docling KB)

Regenerate markdown under `knowledge_base/course/`:

```bash
uv sync --extra kb
uv run --extra kb python scripts/extract_course_kb_docling.py
```

## Orchestration

Emit per-item judge prompts and a manifest:

```bash
uv sync --extra nist-loop
uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py
```

Outputs: `output/nist_graph_loop/prompts/item_01.md` … `item_14.md`, `output/nist_graph_loop/manifest.json`.

## Capture model responses

```bash
uv run python scripts/run_nist_llm_evaluation.py
```

Record human **C / P / N** in `output/results/nist_quiz_scores.json` per `homework-assignment.pdf`.
