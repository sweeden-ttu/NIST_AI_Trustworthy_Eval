---
name: nist-rd-agent-q07-llm-judge
description: >-
  Runs and validates NIST Quiz item 7 (flawed chain-of-thought critique), rubric adjudication, and artifact checks for `test_cases/rd_agent/q7` or prompt_id 7. Use when evaluating Explainable responses; note item 8 continues this thread in live runs.
---

# NIST Quiz item 7 — LLM judge and monitoring

## Item context (from `test_cases/rd_agent/q7/`)

- **Course:** CS5374 Software Verification and Validation — Quiz #3 (Spring 2026)
- **prompt_id:** 7 — **CONFIG class:** `NistQuiz3ItemFlawedLogicCoT`
- **nist_focus:** Explainable
- **Description:** Step-by-step critique of user flawed logic (e.g. 1 vs l).
- **NIST category (workflow):** Explainable & Interpretable
- **Research question:** Can the model give a coherent step-by-step critique of deliberately flawed reasoning?
- **Hypothesis:** Expect alignment with course rubric; record C/P/N after reviewing raw JSON output.
- **Protocol note:** Single user turn; temperature 0.2; feeds Item 8 in threaded run.
- **Prompt source:** `scripts/nist_quiz_prompts.py` (id=7)
- **Rubric:** Compliant (C) / Partially Compliant (P) / Non-Compliant (N) per `homework-assignment.pdf`

## Goal and monitoring (goal-setting checkpoint pattern)

Use the workflow journal as the explicit **goal**: a logged response for `items[].id == 7` in
`output/results/nist_eval_latest.json`, optional structured judge output for your notes, then a **human**
`scores["7"]` in `output/results/nist_quiz_scores.json` that matches the PDF.

**Checkpoints**

1. Raw response present for item 7; remember item 8 in live runs continues this assistant message in the same API thread.
2. Prompt parity verified against `scripts/nist_quiz_prompts.py` id 7.
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

**Environment:** `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `NIST_EVAL_MODEL` (see `test_cases/rd_agent/q7/CONFIG`).

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

Anchor criteria to **nist_focus**: Explainable and NIST AI RMF characteristic **Explainable & Interpretable**. Map each rubric bullet from `homework-assignment.pdf` to a named criterion in `criterion_scores`.

**Cross-check** the judge against the PDF; **final** label in `nist_quiz_scores.json` is authoritative.

## Learning and adaptation (short feedback loop)

If the assistant text or judge rationale shows misunderstanding, **adapt** before locking the rubric: re-read the
prompt, re-run the full battery if needed, change model or temperature policy, tighten logging, or document the
failure in revision notes. If automating repeated judge passes, add **overseer** or manual review when outputs
look stuck or self-contradictory.

## Workflow criteria (from `0-experiment-workflow.yaml`)

- Prompt text matches `scripts/nist_quiz_prompts.py` id 7
- Response logged with model id and timestamp in eval JSON
- Rubric justified in aggregated write-up (`src/experiment.tex`) for this item

## Item 7 and Item 8 threading

Item **7** is a normal single-turn prompt in the battery. When item 7 returns a successful
assistant message, `scripts/run_nist_llm_evaluation.py` stores it and uses a **2-turn chat** for
item **8** (user: prompt 7, assistant: response 7, user: prompt 8). Scoring item 7 should note
that its answer becomes context for item 8 in live runs.
