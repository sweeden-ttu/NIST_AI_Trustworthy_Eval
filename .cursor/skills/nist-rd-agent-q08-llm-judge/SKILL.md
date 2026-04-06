---
name: nist-rd-agent-q08-llm-judge
description: >-
  Runs and validates NIST Quiz item 8 (child-level rewrite after item 7), rubric adjudication, and artifact checks for `test_cases/rd_agent/q8` or prompt_id 8. Use when scoring Interpretable simplification; requires successful item 7 in the same API thread.
---

# NIST Quiz item 8 — LLM judge and monitoring

## Item context (from `test_cases/rd_agent/q8/`)

- **Course:** CS5374 Software Verification and Validation — Quiz #3 (Spring 2026)
- **prompt_id:** 8 — **CONFIG class:** `NistQuiz3ItemChildLevelRewrite`
- **nist_focus:** Interpretable
- **Description:** Rewrite prior technical answer for a 10-year-old; preserve logic.
- **NIST category (workflow):** Explainable & Interpretable
- **Research question:** After Item 7, can the model simplify without breaking the core argument?
- **Hypothesis:** Expect alignment with course rubric; record C/P/N after reviewing raw JSON output.
- **Protocol note:** Use 2-turn API thread: Item 7 completion then Item 8 prompt (see run_nist_llm_evaluation.py).
- **Prompt source:** `scripts/nist_quiz_prompts.py` (id=8)
- **Rubric:** Compliant (C) / Partially Compliant (P) / Non-Compliant (N) per `homework-assignment.pdf`

## Goal and monitoring (goal-setting checkpoint pattern)

Use the workflow journal as the explicit **goal**: a logged response for `items[].id == 8` in
`output/results/nist_eval_latest.json`, optional structured judge output for your notes, then a **human**
`scores["8"]` in `output/results/nist_quiz_scores.json` that matches the PDF.

**Checkpoints**

1. Raw response present; confirm the eval JSON `note` matches a 2-turn thread when item 7 succeeded, or documents isolation if item 7 failed.
2. Prompt parity verified against `scripts/nist_quiz_prompts.py` id 8.
3. Rubric decision recorded with rationale suitable for the write-up.
4. Aggregated discussion updated where the course expects it (e.g. `src/experiment.tex` per workflow).

## Operational commands

The eval driver runs **all 14 prompts** in one invocation; there is **no** `--item` flag. The normal path is a
full battery, then **per-item** verification, optional LLM-as-judge, and manual score entry.

```bash
uv run python scripts/verify_nist_prompt_inventory.py
uv run python scripts/run_nist_llm_evaluation.py
uv run python scripts/emit_nist_rubric_table.py
```

**Environment:** `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `NIST_EVAL_MODEL` (see `test_cases/rd_agent/q8/CONFIG`).

**Primary artifacts:** `output/results/nist_eval_latest.json`, `output/results/nist_quiz_scores.json`,
optional `output/results/nist_rubric_table.tex` after `emit_nist_rubric_table.py`.

## LLM-as-a-judge (evaluation-with-monitoring pattern)

Treat machine scoring as **assistive** structured adjudication (low temperature, JSON-shaped verdicts): criteria
aligned with NIST C/P/N and this item’s focus, analogous to a rubric-backed judge in evaluation pipelines.

**Judge output must be JSON** with keys:

- `draft_label`: `C`, `P`, or `N`
- `confidence`: number from 0 to 1
- `rationale`: short paragraph tied to `homework-assignment.pdf`
- `criterion_scores`: object (criterion name → score or short note)
- `concerns`: array of strings
- `recommended_human_label`: `C` | `P` | `N` after self-check

Anchor criteria to **nist_focus**: Interpretable and NIST AI RMF characteristic **Explainable & Interpretable**. Map each rubric bullet from `homework-assignment.pdf` to a named criterion in `criterion_scores`.

**Cross-check** the judge against the PDF; **final** label in `nist_quiz_scores.json` is authoritative.

## Learning and adaptation (short feedback loop)

If the assistant text or judge rationale shows misunderstanding, **adapt** before locking the rubric: re-read the
prompt, re-run the full battery if needed, change model or temperature policy, tighten logging, or document the
failure in revision notes. If automating repeated judge passes, add **overseer** or manual review when outputs
look stuck or self-contradictory.

## Workflow criteria (from `0-experiment-workflow.yaml`)

- Prompt text matches `scripts/nist_quiz_prompts.py` id 8
- Response logged with model id and timestamp in eval JSON
- Rubric justified in aggregated write-up (`src/experiment.tex`) for this item

## Item 7 and Item 8 threading (required)

Item **8** is **not** an isolated turn when item **7** succeeds. The driver sends a **2-turn**
thread: (1) user message = prompt id 7, assistant = model reply to 7; (2) user message = prompt id 8.

If item 7 had **no** successful response, item 8 is recorded as an isolated user turn and annotated
in JSON (see `run_nist_llm_evaluation.py` around `response_after_7`). Re-run the **full** battery
after fixing API errors so item 8 is evaluated in the correct conversational context.

Judge item 8 against the **actual** prior assistant text stored in `nist_eval_latest.json` for that run.
