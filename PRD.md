# PRD — Quiz #3 write-up completion (adk-ralph / rd-agent scope)

## Problem (historical)

The repository targets **CS5374 Quiz #3**: NIST AI RMF–aligned **14-prompt** LLM evaluation with human **C / P / N** rubric (`homework-assignment.pdf`, `test_cases/CONFIG`). The LaTeX source previously mixed NIST-aligned `main.tex` body with **legacy** `sec/3_results_validation.tex` and `sec/9_meta_review.tex` (applied crypto + old `run_coursework_outputs` / OpenSSL instructions).

## Current state (remediated)

1. **`README.md`** restored as the NIST project runbook; documents **canonical `src/main.tex`** vs legacy **`src/ieee_journal.tex`**, env setup, CI, and optional actionlint.
2. **`src/sec/3_results_validation.tex`** validates **NIST JSON artifacts** (`nist_eval_latest.json`, `nist_quiz_scores.json`, `nist_rubric_table.tex`) and item 7→8 threading; crypto figures removed from this section.
3. **`src/sec/9_meta_review.tex`** meta-review + reproducibility for the **NIST pipeline**; legacy conda/OpenSSL crypto path removed as the default.
4. **`src/ieee_journal.tex`** header comments updated to point authors at **`main.tex`** for Quiz #3.
5. **Artifact traceability** remains the student’s responsibility: run a **live** eval when `dry_run` is true in JSON; rubric keys **1–14** are present in `nist_quiz_scores.json` in-repo.

## Goals (unchanged)

1. **Submission-ready PDF** from `src/main.tex` with no contradictory reproducibility instructions.
2. **Traceability** from prose to `output/results/nist_eval_latest.json` and `nist_quiz_scores.json`.
3. **Honest labeling**: narrow “template” language after a real live run and score refresh.

## Non-goals

- Re-implementing the course autograder.
- Mandating OpenCode or MCP for submission.

## Success metrics

- [x] No default requirement for `conda activate rd-ralph-template && python scripts/run_coursework_outputs.py` for **crypto** in peer-review reproducibility text (`sec/9`).
- [x] `sec/3` discusses **NIST** validation, not AES/TLS figures.
- [x] `README.md` names canonical build target and links `PRD.md` / `todo.json`.

## References

- [`todo.json`](todo.json) — task status and audit notes.
- [`Design.md`](Design.md) — import paths and consolidation notes.
- [`README.md`](README.md) — environment and commands.
