---
name: homework-to-ieee-article
description: Turn CS 6343-style cryptography homework into IEEE or article-class LaTeX with reproducible figures under output/diagrams and JSON under output/results.
---

# Homework → IEEE / article LaTeX

## When to use

- Editing **`homework-assignment.txt`** (in repo root; PDF optional) into a paper.
- Wiring **`src/ieee_journal.tex`** + **`src/sec/*.tex`** *or* **`src/main.tex`** + **`src/experiment.tex`**.
- Keeping **`test_cases/rd_agent/q*/`** workflows aligned with generated artifacts.

## Repository map (this template)

| Role | Path |
|------|------|
| Assignment text | `homework-assignment.txt` (use for MCP `homework_pdf` / `extract_questions`) |
| Coursework driver | `scripts/run_coursework_outputs.py` → `output/results/q1-summary.json`, `output/results/q2/*`, `output/results/q3-cipher-summary.json` + **all** `q*.pdf` under `output/diagrams/` |
| Demo metrics figures | `examples/python/generate_results.py` → `output/results.json`; `examples/python/plot_diagram.py` → `output/diagrams/performance.pdf` and `performance.png` |
| Toy AES | `scripts/toy_aes128_trace.py` |
| IEEE driver | `src/ieee_journal.tex`, `\graphicspath{{../output/diagrams/}}` |
| Article-class driver | `src/main.tex`, same graphics path |
| Results section (IEEE body) | `src/sec/3_results_validation.tex` — includes **every** `output/diagrams/*.pdf` used for the course + `performance.pdf` |
| Results section (main) | `src/experiment.tex` — same coverage |
| Section iteration agents | `test_cases/article_sections/` (`sec_manifest.yaml`, `secNN/agents/*.yaml`); regenerate with `python scripts/generate_article_section_agents.py` |

### Complete `output/diagrams/` inventory (reference in LaTeX)

After running both pipelines, expect at least:

- **Q1:** `q1-hamming-rounds.pdf`, `q1-ablation-shiftrows.pdf`, `q1-ablation-mixcolumns.pdf`
- **Q2:** `q2-ecb-noise.pdf`, `q2-cbc-noise.pdf`, `q2-header-fixed-ecb.pdf`, `q2-header-fixed-cbc.pdf`
- **Q3:** `q3-client-hello-table.pdf`, `q3-server-hello-summary.pdf`
- **Examples:** `performance.pdf`, `performance.png` (PNG optional in PDF build; cite if needed for HTML)

Wireshark placeholders: `output/diagrams/q3-wireshark/README.txt` (not a figure; student captures go here).

## Steps

1. **Ground truth:** `test_cases/rd_agent/q*/CONFIG` + `0-experiment-workflow.yaml`; keep `homework-assignment.txt` authoritative for wording.
2. **Regenerate artifacts:** `conda activate rd-ralph-template && python scripts/run_coursework_outputs.py` then, if demo plots are required, `python examples/python/generate_results.py -q q1 && python examples/python/plot_diagram.py -i output/results.json`.
3. **LaTeX:** Ensure `src/sec/3_results_validation.tex` (IEEE) and/or `src/experiment.tex` (`main.tex`) reference **all** PDFs above; one `\label` per figure; `\ref{}` in Discussion.
4. **Build:** `cd src && latexmk -pdf ieee_journal.tex` *or* `pdflatex main && bibtex main && pdflatex main` (see `README.md`).
5. **Reproducibility:** Record OpenSSL / OS / `openssl version` snippets from `q1-summary.json` / `q2/openssl_run.json` as needed.

## Constraints

- Do not claim production security for educational AES code (`toy_aes128_trace.py`).
- Set `RD_AGENT_MCP_EXEC_AGENTS=true` only in trusted environments (see `skills/rd-agent-mcp-operator/SKILL.md`).
