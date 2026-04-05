# Article section iteration agents (`src/sec`)

YAML specs for **rd-agent** and **adk-ralph** that target each `\input{sec/...}` file in `src/ieee_journal.tex`. Use them for **iterative** improvement: refresh data, revise prose, validate LaTeX, rebuild PDF.

## Prerequisite: regenerate coursework outputs

From the repo root (conda env with `matplotlib`, `numpy`, `pycryptodome`, `Pillow`; `openssl` on `PATH`):

```bash
conda activate rd-ralph-template
python scripts/run_coursework_outputs.py
```

See [`scripts/README.md`](../../scripts/README.md) for details, Q3 network notes, and Q2 key/IV handling.

## Layout

| Path | Purpose |
|------|---------|
| [`sec_manifest.yaml`](./sec_manifest.yaml) | Section index + recommended iteration order |
| [`CONFIG`](./CONFIG) | Template metadata for this bundle |
| `sec00/agents/rd-agent.yaml` … `sec09/agents/adk-ralph.yaml` | One **rd-agent** + one **adk-ralph** spec per section |

Section IDs map to `src/sec/*.tex` (e.g. `sec03` → `3_results_validation.tex`).

## Regenerating agent YAML

If you rename sections or change iteration instructions, re-emit all agent files:

```bash
python scripts/generate_article_section_agents.py
```

## Iteration loop (manual or MCP)

1. Run `run_coursework_outputs.py` so JSON/PDFs match the article.
2. For each `secNN` (typically **sec03** soon after data refresh, then others):
   - Run **rd-agent** with the task in `secNN/agents/rd-agent.yaml` (submodule + LM Studio per [`SUBMODULES.md`](../../SUBMODULES.md)).
   - Merge `output/article_iterations/secNN/rd-agent-revision.tex` into `src/sec/*.tex` (review diff; keep `\section` lines consistent).
   - Optionally run **adk-ralph** from `secNN/agents/adk-ralph.yaml` for tooling around `\includegraphics` checks and reports.
3. `cd src && latexmk -pdf -interaction=nonstopmode ieee_journal.tex`
4. Repeat passes until warnings and factual drift are acceptable.

**Outputs** land under `output/article_iterations/secNN/` (create as needed; safe to gitignore locally).

## Relationship to homework test cases

`test_cases/rd_agent/q{1,2,3}/` drives **assignment** experiments. This folder drives **article polish** for all `src/sec` files after those results exist.
