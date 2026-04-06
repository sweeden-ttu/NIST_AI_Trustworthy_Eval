#!/usr/bin/env python3
"""Emit test_cases/article_sections/secNN/agents/{rd-agent,adk-ralph}.yaml (NIST-first).

Run from repo root: uv run python scripts/generate_article_section_agents.py
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "test_cases" / "article_sections"

SECTIONS: list[dict[str, str]] = [
    {
        "id": "sec00",
        "tex": "src/sec/0_abstract.tex",
        "title": "Executive Summary",
        "rd_focus": (
            "Section focus: **executive synthesis** across **all 14** questionnaire items—themes, "
            "trustworthiness takeaways, and the evaluated **model** string from `nist_eval_latest.json`; "
            "if you summarize compliance, align counts or patterns with `scores` in `nist_quiz_scores.json`. "
            "Explicitly note **item 7→8 threading** if either item is discussed."
        ),
        "adk_note": "Emphasize cross-item coverage (ids 1–14) for any summary claims in this section.",
    },
    {
        "id": "sec01",
        "tex": "src/sec/1_technical_contribution.tex",
        "title": "Technical Contribution",
        "rd_focus": (
            "Section focus: articulate the **technical contribution** as NIST-aligned trustworthy-AI "
            "evaluation / red-teaming of an LLM using the full 14-prompt battery; ground claims in "
            "`nist_eval_latest.json`, scoring methodology in `homework-assignment.pdf`, and `nist_quiz_scores.json`."
        ),
        "adk_note": "Flag claims of novelty that are not supported by the eval artifacts.",
    },
    {
        "id": "sec02",
        "tex": "src/sec/2_experimental_methodology.tex",
        "title": "Experimental Methodology",
        "rd_focus": (
            "Section focus: **reproducible methodology**—how `uv run python scripts/run_nist_llm_evaluation.py` "
            "was executed; document defaults `OPENAI_BASE_URL=http://localhost:1234/v1` and "
            "`NIST_EVAL_MODEL=unrestricted-knowledge-will-not-refuse-15b` (or overrides), temperature, "
            "environment configuration and how human adjudication produced `nist_quiz_scores.json`; cite "
            "`scripts/nist_quiz_prompts.py` for prompt parity."
        ),
        "adk_note": "Check that described driver and env vars match keys present in `nist_eval_latest.json` (model, base_url, temperature).",
    },
    {
        "id": "sec03",
        "tex": "src/sec/3_results_validation.tex",
        "title": "Results and Claims Validation",
        "rd_focus": (
            "Section focus: **tabular and narrative validation**—each row or claim maps to **item id 1–14**; "
            "labels **C/P/N** must match `nist_quiz_scores.json` exactly; prose about behavior must be faithful "
            "to `response` text in `nist_eval_latest.json`. If `nist_rubric_table.tex` exists, keep table and prose consistent."
        ),
        "adk_note": "Build a checklist mapping each \\textbf{item} or table row mentioned to a concrete id 1–14 and score key.",
    },
    {
        "id": "sec04",
        "tex": "src/sec/4_literature_review.tex",
        "title": "Literature Review and Positioning",
        "rd_focus": (
            "Section focus: connect related work to **NIST AI RMF** trustworthiness characteristics "
            "(valid/reliable, safe, secure & resilient, explainable/interpretable, privacy-enhanced, fair, accountable & transparent) "
            "as reflected in the questionnaire. **Do not** treat legacy crypto coursework as primary empirical ground truth unless the section explicitly cites it."
        ),
        "adk_note": "Optional: verify cited external sources are formatted consistently; NIST artifact paths are not bibliography entries.",
    },
    {
        "id": "sec05",
        "tex": "src/sec/5_presentation_clarity.tex",
        "title": "Presentation and Clarity",
        "rd_focus": (
            "Section focus: **clarity and consistency**—define C/P/N once, consistent model naming, "
            "smooth transitions; remove contradictions with `nist_quiz_scores.json` or `nist_eval_latest.json`."
        ),
        "adk_note": "Scan for contradictory labels (same item id described with different C/P/N).",
    },
    {
        "id": "sec06",
        "tex": "src/sec/6_detailed_comments.tex",
        "title": "Detailed Technical Comments",
        "rd_focus": (
            "Section focus: **item-level commentary**—clusters (e.g., Safe, Fair) with specifics tied to "
            "`nist_eval_latest.json` responses and the corresponding human scores; avoid generic boilerplate."
        ),
        "adk_note": "For each discussed item id, confirm a non-empty `response` field exists in eval JSON (unless documenting API failure).",
    },
    {
        "id": "sec07",
        "tex": "src/sec/7_questions_authors.tex",
        "title": "Questions for Authors",
        "rd_focus": (
            "Section focus: **author-facing questions** grounded in ambiguity, rubric edge cases, or "
            "limitations visible in raw `nist_eval_latest.json` responses and `nist_quiz_scores.json`."
        ),
        "adk_note": "Ensure questions reference concrete item ids or observable model behaviors where possible.",
    },
    {
        "id": "sec08",
        "tex": "src/sec/8_minor_issues.tex",
        "title": "Minor Issues",
        "rd_focus": (
            "Section focus: **minor prose and LaTeX**—typos, reference hygiene, and \\includegraphics paths: "
            "only require on-disk files when this section actually references figures."
        ),
        "adk_note": "List \\includegraphics paths in this section file and mark missing targets without deleting figure environments.",
    },
    {
        "id": "sec09",
        "tex": "src/sec/9_meta_review.tex",
        "title": "Meta-Review and Integration",
        "rd_focus": (
            "Section focus: **meta-review**—integrate the paper with the NIST evaluation outcome; limitations "
            "and future work must align with documented scores and representative responses; mention item 7→8 protocol where relevant."
        ),
        "adk_note": "Cross-check meta-review claims against full 1–14 coverage in eval JSON and score keys.",
    },
]

RD_PREFIX = """Iterative refinement pass for IEEEtran article section `{title}` in `{tex}`. **Prerequisites:** the full 14-prompt NIST Quiz battery has been run. **Primary ground truth:** `output/results/nist_eval_latest.json` (top-level `items` with numeric `id` 1–14, each with `prompt`, `response`, `error`; item 8 may include a `note` about the 2-turn thread after item 7), `output/results/nist_quiz_scores.json` (object `scores` whose JSON keys are the strings 1 through 14 and values are `C`, `P`, or `N` per `homework-assignment.pdf`), optional `output/results/nist_rubric_table.tex`, and prompt text parity via `scripts/nist_quiz_prompts.py`. **Rubric source of truth:** `homework-assignment.pdf` (repo root). """

RD_SUFFIX = r""" **Common goals:** keep LaTeX IEEE-safe; use \strength, \weakness, \suggestion macros from `src/review_macros.tex` where this section uses review-style annotations. **Artifact refresh:** `python scripts/run_coursework_outputs.py` runs the live NIST driver by default and emits rubric TeX when scores exist—per `test_cases/CONFIG`; use `--skip-nist-eval` to skip the driver. Do not treat legacy toy-crypto figures or q1–q3 coursework JSON as ground truth unless this section explicitly cites them. **Output:** write a merge-ready snippet to `output/article_iterations/{sec_id}/rd-agent-revision.tex` (section body only, no \documentclass)."""


def rd_agent_yaml(sec: dict[str, str]) -> str:
    sec_id = sec["id"]
    body = RD_PREFIX.format(title=sec["title"], tex=sec["tex"]) + sec["rd_focus"] + RD_SUFFIX.format(sec_id=sec_id)
    return f"""agent:
  name: rd-agent-article-{sec_id}
  type: rd-agent
  model: ibm/granite-4-h-tiny
  embedding_model: text-embedding-nomic-embed-text-v1.5
  provider: lm_studio

command:
  module: rdagent
  scenario: data_science
  args:
    - --task
    - >-
      {body}
    - --output
    - output/article_iterations/{sec_id}/rd-agent

environment:
  LM_STUDIO_BASE_URL: http://192.168.0.13:1234/v1
  LITELLM_OPENAI_API_BASE: http://192.168.0.13:1234/v1
  OPENAI_API_BASE: http://192.168.0.13:1234/v1
  LITELLM_OPENAI_API_KEY: lm-studio
  EMBEDDING_MODEL: text-embedding-nomic-embed-text-v1.5

chroma:
  collection: research
  metadata:
    phase: article_iteration
    question_id: article-{sec_id}
    agent_type: rd-agent
    section_tex: {sec["tex"]}

tools:
  - name: file_write
    description: Revised section snippet (LaTeX body)
    output: output/article_iterations/{sec_id}/rd-agent-revision.tex
  - name: json_write
    description: Optional structured diff notes / checklist
    output: output/article_iterations/{sec_id}/revision-notes.json

retry:
  max_attempts: 3
  backoff: exponential

timeout: 600

llm_calls:
  - purpose: section_audit
    model: ibm/granite-4-h-tiny
    prompt_template: |
      Section `{sec["title"]}` (`{sec["tex"]}`). Current text:
      ---
      {{section_source}}
      ---
      List concrete mismatches vs NIST artifacts (`output/results/nist_eval_latest.json`, `output/results/nist_quiz_scores.json`, optional `output/results/nist_rubric_table.tex`, `homework-assignment.pdf`, `scripts/nist_quiz_prompts.py`). Flag any claim not supported by those sources. JSON only.
  - purpose: section_rewrite
    model: ibm/granite-4-h-tiny
    prompt_template: |
      Apply fixes from audit: {{audit}}
      Produce improved LaTeX fragment for the same section, preserving \\section heading line.
"""


def adk_agent_yaml(sec: dict[str, str]) -> str:
    sec_id = sec["id"]
    note = sec["adk_note"]
    return f"""agent:
  name: adk-ralph-article-{sec_id}
  type: adk-ralph
  model: granite4:3b
  provider: ollama

command:
  binary: cargo
  args:
    - run
    - --
    - >-
      NIST consistency + LaTeX hygiene for `{sec["tex"]}` ({sec["title"]}). Under `output/article_iterations/{sec_id}/adk-ralph/`, add or run a small helper (Rust or Python) that: (1) Verifies `output/results/nist_eval_latest.json` exists and that `items[].id` covers integers 1–14 uniquely; (2) Verifies `output/results/nist_quiz_scores.json` contains `scores` with every JSON key from the strings 1 through 14; (3) Strips trailing whitespace and checks brace balance on the section .tex file; (4) Lists paths from \\includegraphics commands in that section and reports only missing files that are actually referenced; (5) Emits `report.md` and `latex-hygiene.json` with findings. Mention item 7→8 threading if item 8 appears in eval JSON. Section-specific emphasis: {note} Do not remove substantive narrative; structural fixes and reports only. Re-run after a fresh `uv run python scripts/run_nist_llm_evaluation.py` when raw responses change.
  working_dir: output/article_iterations/{sec_id}/adk-ralph

environment:
  OLLAMA_HOST: http://localhost:11434
  RALPH_MODEL_PROVIDER: ollama
  RALPH_LOCAL_MODEL: granite4:3b

chroma:
  collection: research
  metadata:
    phase: article_iteration
    question_id: article-{sec_id}
    agent_type: adk-ralph
    section_tex: {sec["tex"]}

tools:
  - name: generate_json
    description: Machine-readable report (JSON coverage, graphics paths, warnings)
    output: output/article_iterations/{sec_id}/adk-ralph/latex-hygiene.json

artifacts:
  - prd.md
  - design.md
  - tasks.json

retry:
  max_attempts: 2
  backoff: linear

timeout: 900

phases:
  prd:
    prompt: |
      PRD: validate `{sec["tex"]}` against NIST eval JSON, rubric scores JSON, and basic LaTeX sanity. {note}
  architect:
    prompt: |
      Design: parse eval JSON for items 1–14; parse scores keys; parse .tex for includegraphics; write Markdown + JSON under output/article_iterations/{sec_id}/adk-ralph/.
  loop:
    prompt: |
      Implement minimal CLI; document rerun after `uv run python scripts/run_nist_llm_evaluation.py` when updating raw responses.
"""


def main() -> None:
    for sec in SECTIONS:
        sec_id = sec["id"]
        agents_dir = ARTICLE / sec_id / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "rd-agent.yaml").write_text(rd_agent_yaml(sec), encoding="utf-8")
        (agents_dir / "adk-ralph.yaml").write_text(adk_agent_yaml(sec), encoding="utf-8")
    print(f"Wrote {len(SECTIONS) * 2} agent YAMLs under {ARTICLE}")


if __name__ == "__main__":
    main()
