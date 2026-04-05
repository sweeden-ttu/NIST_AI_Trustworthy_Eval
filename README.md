# Research Template

A GitHub template for academic work that combines an **IEEE-style article**, **CS homework–driven experiments**, and **LLM agents** (`rd-agent`, `adk-ralph`) orchestrated via **[rd-agent-mcp](https://github.com/sweeden-ttu/rd-agent-mcp)** (CLI + MCP).

## Overview

- **rd-agent** — Microsoft R&D Agent (research / data-science scenarios), as a submodule under `agents/rd-agent`.
- **adk-ralph** — Multi-agent codegen (Rust-first workflow), as a submodule under `agents/adk-ralph`.
- **rd-agent-mcp** — Phases, LangGraph pipeline, Chroma embeddings, `run_agent_pipeline` / `compile_results` (install separately; not a submodule here).
- **ChromaDB / LM Studio** — Local embeddings and chat via OpenAI-compatible endpoints.

Submodule URLs and setup: **[SUBMODULES.md](./SUBMODULES.md)**.

## Quick Start

### 1. Create a new repository

Use GitHub **“Use this template”** on this repo.

### 2. Clone and init submodules

```bash
git clone https://github.com/YOUR_NAME/your-research-repo
cd your-research-repo
git submodule update --init --recursive
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` (see [`.env.example`](./.env.example)):

- `LM_STUDIO_BASE_URL`, `CHAT_MODEL`, `EMBEDDING_MODEL`
- `RD_AGENT_PATH`, `ADK_RALPH_PATH` (default `./agents/rd-agent`, `./agents/adk-ralph`)

LM Studio agent template (optional): [`config/lmstudio-granite-agent-to-agent.jinja`](./config/lmstudio-granite-agent-to-agent.jinja) — details in [`config/README.md`](./config/README.md).

### 4. Article source (IEEE)

- **Driver:** [`src/ieee_journal.tex`](./src/ieee_journal.tex) (IEEEtran).
- **Body sections:** [`src/sec/`](./src/sec/) — numbered `0_abstract.tex` … `9_meta_review.tex` (multi-section layout, peer-review–style annotations via [`src/review_macros.tex`](./src/review_macros.tex)).
- **Coursework monograph (article class):** [`src/main.tex`](./src/main.tex) pulls in [`intro_zyf.tex`](./src/intro_zyf.tex), [`prelim.tex`](./src/prelim.tex), [`method_zyf.tex`](./src/method_zyf.tex), [`experiment.tex`](./src/experiment.tex), [`conclusion.tex`](./src/conclusion.tex), [`reproducibility.tex`](./src/reproducibility.tex), [`ethics.tex`](./src/ethics.tex), [`appendix.tex`](./src/appendix.tex), plus [`main.bib`](./src/main.bib) / [`main.bbl`](./src/main.bbl) (BibTeX) and local [`natbib.sty`](./src/natbib.sty) / [`fancyhdr.sty`](./src/fancyhdr.sty) on the path. Build: `cd src && pdflatex main && bibtex main && pdflatex main && pdflatex main`.
- **Legacy ICLR-style tree:** [`src/archive/rd-agent-paper/`](./src/archive/rd-agent-paper/).

### 5. Builds (GitHub Actions)

- **IEEE article:** workflow **“Build IEEE PDF”** — triggers on changes under `src/**/*.tex` (see [`.github/workflows/build-ieee-pdf.yml`](./.github/workflows/build-ieee-pdf.yml)).
- Other workflows: **Research Pipeline**, **Agent Demo**, **Build LaTeX PDF** (archive paper path) — see `.github/workflows/`.

## Research pipeline (rd-agent-mcp)

Install the package, then use Typer commands (names use **kebab-case** on the CLI):

```bash
pip install -e /path/to/rd-agent-mcp   # or your install method

rd-agent-mcp run-phase questions
rd-agent-mcp run-phase experiment
rd-agent-mcp run-phase embeddings
rd-agent-mcp run-phase agent
rd-agent-mcp run-phase results

rd-agent-mcp research-phase --topic "Your topic" --homework-pdf homework-assignment.txt
```

| Phase | Description | Agents / tools |
|-------|-------------|----------------|
| Questions | Extract questions from homework/papers | rd-agent (LLM) |
| Experiment | Design experiments | rd-agent + prompts |
| Embeddings | Chroma + embeddings | LM Studio |
| Agent | Run or simulate agents | rd-agent + adk-ralph (if enabled) |
| Results | Compile JSON / LaTeX sections | Pipeline |

**MCP:** set server `cwd` to this repo when calling tools so paths like `homework-assignment.txt` resolve. Snippets: [`mcp/examples/`](./mcp/examples/) (e.g. [`mcp-tool-pipeline.md`](./mcp/examples/mcp-tool-pipeline.md), [`mcp-tool-payloads.json`](./mcp/examples/mcp-tool-payloads.json)).

## Test cases

YAML workflows and per-question configs for the homework → article thread:

**Article sections (`src/sec`):** iterative rd-agent / adk-ralph specs live under [`test_cases/article_sections/`](./test_cases/article_sections/README.md) (regenerate with `python scripts/generate_article_section_agents.py`).

```
test_cases/
├── CONFIG
├── rd_agent/
│   ├── mcp-graph-hw1-manifest.yaml
│   ├── q1/
│   │   ├── CONFIG
│   │   ├── agents/
│   │   │   ├── rd-agent-survey.yaml
│   │   │   └── adk-ralph-survey.yaml
│   │   └── 0-experiment-workflow.yaml
│   ├── q2/
│   │   ├── CONFIG
│   │   ├── agents/ …
│   │   └── 0-experiment-workflow.yaml
│   └── q3/
│       ├── CONFIG
│       ├── agents/ …
│       └── 0-experiment-workflow.yaml
├── article_sections/        # per src/sec/*.tex iteration agents (sec00–sec09)
│   ├── README.md
│   ├── sec_manifest.yaml
│   └── secNN/agents/
```

Validate:

```bash
rd-agent-mcp validate-tests --test-dir test_cases
python -m rd_agent_mcp.test_runner --test-dir test_cases --question q1
```

## Homework seed → IEEE narrative (CS 6343-style)

- **Assignment text:** `homework-assignment.txt` (committed). Add `homework-assignment.pdf` locally if you use PDF extractors.
- **Assets:** e.g. `Secret.bmp` — see [`assets/README.md`](./assets/README.md).
- **Figures / JSON:** `scripts/run_coursework_outputs.py` → `output/diagrams/`, `output/results/` (see article `\graphicspath` in `src/ieee_journal.tex`).

## Examples (no agents required)

- **Python:** [`examples/python/`](./examples/python/) — `generate_results.py`, `plot_diagram.py`.
- **Rust:** [`examples/rust/`](./examples/rust/) — `analyze_stats` CLI ([`examples/README.md`](./examples/README.md)).

## MCP examples and skills

- [`mcp/examples/`](./mcp/examples/) — pipelines, LM Studio notes, agent shell checks.
- [`skills/`](./skills/) — Cursor `SKILL.md` files; install per [`skills/README.md`](./skills/README.md).

## Cursor + LM Studio model sync

```bash
python3 scripts/sync_cursor_lmstudio_models.py --union-lms --backup
```

Details: [`scripts/README.md`](./scripts/README.md).

## GitHub Actions (summary)

| Workflow | Purpose |
|----------|---------|
| **Build IEEE PDF** | `latexmk` on `src/ieee_journal.tex` |
| **Research Pipeline** | Manual phase runs, optional test validation |
| **Agent Demo** | Python / Rust / LaTeX demo jobs |
| **Build LaTeX PDF** | Archive / full paper build path |

## Directory structure

```
.
├── .github/workflows/       # CI (IEEE PDF, research pipeline, demos, archive PDF)
├── SUBMODULES.md            # agents/rd-agent + agents/adk-ralph
├── src/
│   ├── ieee_journal.tex
│   ├── review_macros.tex
│   ├── sec/                  # 0_abstract … 9_meta_review
│   └── archive/rd-agent-paper/
├── mcp/examples/
├── skills/
├── test_cases/
│   ├── rd_agent/             # q1–q3 homework workflows
│   └── article_sections/     # ieee_journal sec/*.tex iteration agents
├── agents/                   # git submodules (rd-agent, adk-ralph)
├── assets/
├── config/
├── examples/                 # python/, rust/
├── scripts/
├── output/                   # generated (often gitignored)
└── README.md
```

## License

CC-BY 4.0 — see [LICENSE](./LICENSE).
