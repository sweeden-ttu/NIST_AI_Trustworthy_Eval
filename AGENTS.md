# AGENTS.md — repository map and agent workflows

Quick orientation for AI coding agents working in this repo. **End-to-end human commands** are in [`README.md`](README.md).

## Top-level layout

| Path | Role |
|------|------|
| [`src/`](src/) | LaTeX article: `main.tex`, `sec/*.tex`, bibliography; build artifacts (`*.pdf`, `*.aux`, …) may appear here. |
| [`scripts/`](scripts/) | Executable tooling: NIST eval (`run_nist_llm_evaluation.py`, `nist_quiz_prompts.py`), orchestration (`run_coursework_outputs.py`, `nist_experiment_graph_loop.py`), rubric (`emit_nist_rubric_table.py`), course KB (`extract_course_kb_docling.py`), helpers. |
| [`test_cases/`](test_cases/) | **`CONFIG`** — quiz index (`order`, `metadata`, `paths`). **`rd_agent/qN/`** — per-question `CONFIG` + `0-experiment-workflow.yaml`. **`article_sections/`** — section agents and manifest. **`latex_sections_critique/`** — JSON LaTeX critique bundle. |
| [`output/`](output/) | Generated results: `output/results/*.json`, `nist_graph_loop/`, `article_iterations/`, etc. Treat as **volatile**; may contain secrets if user runs local crypto demos—do not assume safe to commit. |
| [`knowledge_base/`](knowledge_base/) | **`opencode/`** — judge/instructor system prompts, run templates, recommended models. **`course/`** — Docling-derived markdown from instructor materials. |
| [`agents/rd-agent-mcp/`](agents/rd-agent-mcp/) | Python package + MCP server (`rd-agent-mcp` on PyPI / local install); LangGraph research graph, phases, LaTeX critique tools. |
| [`.github/workflows/`](.github/workflows/) | `research-pipeline.yaml`, `agent-demo.yaml`, `build-pdf.yaml`. Secrets catalog: [`.github/SECRETS.md`](.github/SECRETS.md). |
| [`.cursor/skills/`](.cursor/skills/) | Project Cursor skills (NIST q01–q14 judges, `/init`, `/workflows`, etc.). |

## Planning and environment extras

- [`todo.json`](todo.json), [`PRD.md`](PRD.md), [`Design.md`](Design.md) — `/init` outputs for **adk-ralph**: stale “template”/crypto LaTeX vs NIST JSON alignment.
- [`environment.yml`](environment.yml) — Conda env with `pip install -e ./agents/rd-agent-mcp`.

## Key files

- [`pyproject.toml`](pyproject.toml) — root package; **editable** `rd-agent-mcp` via `[tool.uv.sources]`; optional extras: `kb`, `graph`, `nist-loop`. **Python >= 3.11**.
- [`opencode.json`](opencode.json) — default OpenCode project model/provider hints.
- [`test_cases/CONFIG`](test_cases/CONFIG) — canonical paths for eval JSON, rubric JSON/TeX, question root.
- [`.env.example`](.env.example) — template for LM Studio / OpenAI-compatible URLs and model ids.

## Execution surfaces (short)

- **NIST battery**: `python scripts/run_nist_llm_evaluation.py` (`--dry-run` or live with env vars).
- **Orchestrator**: `python scripts/run_coursework_outputs.py` ([`--nist-live`](scripts/run_coursework_outputs.py)).
- **Judge prompt bundle**: `uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py`.
- **Regenerate article YAML agents**: `uv run python scripts/generate_article_section_agents.py`.
- **MCP**: **`user-rd-agent-mcp`** in Cursor — read tool schemas under the IDE’s `mcps/user-rd-agent-mcp/tools/*.json` before calling tools.

## Conventions

- **Question ids**: strings `q1`…`q14` in layouts; NIST JSON uses numeric item ids **1–14**; items **7→8** may be a threaded conversation in the driver.
- **Rubric**: human-only **C / P / N** in `output/results/nist_quiz_scores.json`; source of truth for definitions: `homework-assignment.pdf`.
- **Prefer `uv`** over raw `pip` for project-documented flows with extras.

---

## OpenCode / judge and instructor role

This repository’s active homework track is the **14-item NIST-style trustworthy AI questionnaire** (`scripts/nist_quiz_prompts.py`, `test_cases/rd_agent/q1`–`q14`).

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

## Orchestration (LangGraph loop)

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

## Security

- Do not commit API keys; use `.env` (untracked) and GitHub **Secrets** per [`.github/SECRETS.md`](.github/SECRETS.md).
- Review `output/` before suggesting `git add` (eval JSON, manifests, or legacy crypto artifacts may be sensitive or large).
