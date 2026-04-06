# Design — LaTeX consolidation for NIST Quiz #3 (adk-ralph)

## Context

- **Primary narrative** is already in `experiment.tex` (per-item question / hypothesis / experiment / rubric result) driven by packaged scores.
- **IEEE-style section files** under `src/sec/` power `test_cases/article_sections` agent YAMLs but **sec03** and **sec09** content predates the NIST-first track.
- **Module layout (Python)**: the research MCP package lives at `agents/rd-agent-mcp`; import path is **`rd_agent_mcp`** (underscore), e.g. `rd_agent_mcp.graph.edges` — not `rdagent`.

```bash
# After: uv sync   OR   conda env create -f environment.yml
python -c "import rd_agent_mcp.graph.edges as e; print(e.__file__)"
rd-agent-mcp --help
```

## Architecture decision: single body story

1. Keep **`src/main.tex`** as the student article entry (article class + `experiment.tex`).
2. **Either** refactor `sec/3_results_validation.tex` into a NIST validation section **or** stop `\\input`-ing it from any build that ships for Quiz #3, and regenerate article agent prompts accordingly.
3. **sec/9_meta_review.tex**: replace crypto meta-review with integration across **14 prompts**, item 7→8 threading, and reproducibility via `scripts/run_nist_llm_evaluation.py` + `run_coursework_outputs.py`.

## Data flow

```text
homework-assignment.pdf (rubric prose)
       ↓
scripts/nist_quiz_prompts.py  →  run_nist_llm_evaluation.py  →  nist_eval_latest.json
       ↓
human review  →  nist_quiz_scores.json  →  emit_nist_rubric_table.tex  →  experiment.tex / sec03
```

## adk-ralph task pattern

For each stale `.tex` file:

1. Read ground truth JSON (items 1–14).
2. Patch LaTeX to cite file paths from `test_cases/CONFIG` `paths` keys.
3. Remove figure environments that reference missing `output/diagrams/*.pdf` **or** gate them behind `\\IfFileExists`.
4. Run `latexmk` locally or rely on `build-pdf.yaml`.

## Dependencies

- Root **`pyproject.toml`** editable-depends on **`agents/rd-agent-mcp`** (`requires-python >= 3.11`).
- **`environment.yml`** creates a Conda env with `pip install -e ./agents/rd-agent-mcp` for parity with CI’s `pip install rd-agent-mcp`.

## Risks

- **Dual track**: if crypto coursework is still required side-by-side, document two reproducibility subsections instead of deleting crypto content outright.
- **PDF homework**: automated diff vs `homework-assignment.pdf` needs `pypdf` or Docling; human verification remains authoritative.
