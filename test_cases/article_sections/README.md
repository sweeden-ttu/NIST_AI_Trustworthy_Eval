# Article section iteration agents (`src/sec`)

YAML specs for **rd-agent** and **adk-ralph** that target each `\input{sec/...}` file in `src/ieee_journal.tex`. Use them for **iterative** improvement after NIST evaluation artifacts exist: align prose with raw responses, scores, and the course rubric PDF, then validate LaTeX.

## Prerequisite: NIST evaluation artifacts

From the **repository root** (Python 3.10+; API key and base URL as in `scripts/run_nist_llm_evaluation.py`):

```bash
uv run python scripts/run_nist_llm_evaluation.py --dry-run
uv run python scripts/run_nist_llm_evaluation.py
```

Record Compliant (C) / Partially Compliant (P) / Non-Compliant (N) in `output/results/nist_quiz_scores.json` per `homework-assignment.pdf`. Optional LaTeX fragment from scores:

```bash
uv run python scripts/emit_nist_rubric_table.py
```

Canonical prompt text lives in `scripts/nist_quiz_prompts.py`. **Note:** the driver runs the **full** battery in one invocation (no `--item` flag); per-item work is verification, rubric justification, and write-up on the produced JSON.

**Special case:** item **8** is evaluated in a **2-turn** API thread after item **7** (see `scripts/run_nist_llm_evaluation.py`).

Legacy coursework scripts (e.g. toy AES / OpenSSL demos) are **not** prerequisites unless the manuscript still cites those results; primary ground truth for the NIST track is the eval JSON, scores, optional `nist_rubric_table.tex`, and the PDF rubric.

## Layout

| Path | Purpose |
|------|---------|
| [`sec_manifest.yaml`](./sec_manifest.yaml) | Section index + recommended iteration order |
| [`CONFIG`](./CONFIG) | Template metadata for this bundle |
| `sec00/agents/rd-agent.yaml` … `sec09/agents/adk-ralph.yaml` | One **rd-agent** + one **adk-ralph** spec per section |

Section IDs map to `src/sec/*.tex` (e.g. `sec03` → `3_results_validation.tex`).

## Regenerating agent YAML

If you change section titles in `sec_manifest.yaml` or adjust NIST-first templates, re-emit all agent files:

```bash
uv run python scripts/generate_article_section_agents.py
```

Review diffs before committing; section-specific goals are encoded in the generator.

## Iteration loop (manual or MCP)

1. Run the NIST eval driver and update `nist_quiz_scores.json` (and optionally `emit_nist_rubric_table.py`).
2. For each `secNN` (often **sec03** first, then **sec00** / **sec09**, then others):
   - Run **rd-agent** with the task in `secNN/agents/rd-agent.yaml`.
   - Merge `output/article_iterations/secNN/rd-agent-revision.tex` into `src/sec/*.tex` (review diff; keep `\section` lines consistent).
   - Optionally run **adk-ralph** for JSON coverage checks, `\includegraphics` existence (when the section uses figures), and LaTeX hygiene reports.
3. `cd src && latexmk -pdf -interaction=nonstopmode ieee_journal.tex`
4. Repeat until warnings and factual drift are acceptable.

**Outputs** land under `output/article_iterations/secNN/` (create as needed; safe to gitignore locally).

## Relationship to homework test cases

`test_cases/rd_agent/q1`–`q14/` describe the **NIST questionnaire** items. This folder drives **article polish** for all `src/sec` files **after** eval JSON and scores exist.
