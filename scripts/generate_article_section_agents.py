#!/usr/bin/env python3
"""Emit test_cases/article_sections/secNN/agents/*.yaml for iterative ieee_journal section refinement."""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = ROOT / "test_cases" / "article_sections"

SECTIONS: list[tuple[str, str, str]] = [
    ("sec00", "0_abstract.tex", "Executive Summary"),
    ("sec01", "1_technical_contribution.tex", "Technical Contribution"),
    ("sec02", "2_experimental_methodology.tex", "Experimental Methodology"),
    ("sec03", "3_results_validation.tex", "Results and Claims Validation"),
    ("sec04", "4_literature_review.tex", "Literature Review and Positioning"),
    ("sec05", "5_presentation_clarity.tex", "Presentation and Clarity"),
    ("sec06", "6_detailed_comments.tex", "Detailed Technical Comments"),
    ("sec07", "7_questions_authors.tex", "Questions for Authors"),
    ("sec08", "8_minor_issues.tex", "Minor Issues"),
    ("sec09", "9_meta_review.tex", "Meta-Review and Integration"),
]


def rd_yaml(sid: str, tex: str, title: str) -> str:
    task = f"""\
      Iterative refinement pass for IEEEtran article section `{title}` in `src/sec/{tex}`.
      Ground truth artifacts (regenerate with `python scripts/run_coursework_outputs.py`):
      `output/results/q1-summary.json`, `output/results/q2/openssl_run.json`,
      `output/results/q3-cipher-summary.json`, and PDFs under `output/diagrams/`
      (especially q1-*.pdf, q2-*.pdf, q3-*.pdf cited from Results).
      Goals: (1) Align prose and numbers with JSON/PDFs; (2) keep LaTeX IEEE-safe;
      (3) use \\strength, \\weakness, \\suggestion macros from src/review_macros.tex where
      this section uses review-style annotations; (4) fix figure paths/labels/captions to match repo layout;
      (5) flag any claim not supported by the toy AES / OpenSSL / openssl s_client methodology.
      Output: write a merge-ready snippet to output/article_iterations/{sid}/rd-agent-revision.tex
      (section body only, no documentclass)."""
    task = textwrap.dedent(task).strip().replace("\n", " ")

    return f"""agent:
  name: rd-agent-article-{sid}
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
      {task}
    - --output
    - output/article_iterations/{sid}/rd-agent

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
    question_id: article-{sid}
    agent_type: rd-agent
    section_tex: src/sec/{tex}

tools:
  - name: file_write
    description: Revised section snippet (LaTeX body)
    output: output/article_iterations/{sid}/rd-agent-revision.tex
  - name: json_write
    description: Optional structured diff notes / checklist
    output: output/article_iterations/{sid}/revision-notes.json

retry:
  max_attempts: 3
  backoff: exponential

timeout: 600

llm_calls:
  - purpose: section_audit
    model: ibm/granite-4-h-tiny
    prompt_template: |
      Section `{title}` (`src/sec/{tex}`). Current text:
      ---
      {{section_source}}
      ---
      List concrete mismatches vs coursework outputs (paths above) and missing citations.
      JSON only.
  - purpose: section_rewrite
    model: ibm/granite-4-h-tiny
    prompt_template: |
      Apply fixes from audit: {{audit}}
      Produce improved LaTeX fragment for the same section, preserving \\section heading line.
"""


def adk_yaml(sid: str, tex: str, title: str) -> str:
    cargo_task = f"""\
      LaTeX hygiene pass for `src/sec/{tex}` ({title}) in ieee_journal project.
      Add or run a small Rust or Python helper under `output/article_iterations/{sid}/adk-ralph/`
      that: (1) strips trailing whitespace / checks brace balance on the section file;
      (2) lists \\includegraphics paths and verifies files exist under output/diagrams/;
      (3) emits a short `report.md` with suggested patches (diff-style or line numbers).
      Do not remove content; only structural and consistency fixes."""
    cargo_task = textwrap.dedent(cargo_task).strip().replace("\n", " ")

    return f"""agent:
  name: adk-ralph-article-{sid}
  type: adk-ralph
  model: granite4:3b
  provider: ollama

command:
  binary: cargo
  args:
    - run
    - --
    - {cargo_task}
  working_dir: output/article_iterations/{sid}/adk-ralph

environment:
  OLLAMA_HOST: http://localhost:11434
  RALPH_MODEL_PROVIDER: ollama
  RALPH_LOCAL_MODEL: granite4:3b

chroma:
  collection: research
  metadata:
    phase: article_iteration
    question_id: article-{sid}
    agent_type: adk-ralph
    section_tex: src/sec/{tex}

tools:
  - name: generate_json
    description: Machine-readable report (graphics paths, warnings)
    output: output/article_iterations/{sid}/adk-ralph/latex-hygiene.json

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
      PRD: tool to validate `src/sec/{tex}` against repo figure paths and basic LaTeX sanity.
  architect:
    prompt: |
      Design: parse .tex for includegraphics, existence-check under ../output/diagrams from src/;
      output Markdown report in output/article_iterations/{sid}/adk-ralph/.
  loop:
    prompt: |
      Implement minimal CLI; document rerun after each `python scripts/run_coursework_outputs.py`.
"""


def main() -> None:
    for sid, tex, title in SECTIONS:
        d = OUT_BASE / sid / "agents"
        d.mkdir(parents=True, exist_ok=True)
        (d / "rd-agent.yaml").write_text(rd_yaml(sid, tex, title), encoding="utf-8")
        (d / "adk-ralph.yaml").write_text(adk_yaml(sid, tex, title), encoding="utf-8")
    print(f"Wrote {len(SECTIONS) * 2} agent files under {OUT_BASE}/sec00..sec09/agents/")


if __name__ == "__main__":
    main()
