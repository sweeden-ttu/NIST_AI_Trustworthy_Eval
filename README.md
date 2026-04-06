# NIST AI Trustworthy Evaluation

Courseware and tooling for a **14-prompt NIST-style trustworthy-AI questionnaire** (Quiz #3), LaTeX write-up under `src/`, optional **OpenCode** judge prompts, and **GitHub Actions** pipelines.

## Prerequisites

- **Python 3.11+** (required for the editable **`rd-agent-mcp`** dependency under `agents/rd-agent-mcp/`; matches CI).
- **`uv`** (recommended) or **Miniconda/Mamba** using [`environment.yml`](environment.yml); plain `pip` works if you install packages manually.
- **OpenAI-compatible API** for live model calls: e.g. **LM Studio** on `http://localhost:1234/v1`, or a cloud provider (`OPENAI_API_KEY` required). CI can check the 14-prompt inventory without a key via `scripts/verify_nist_prompt_inventory.py`.
- **Optional — LaTeX**: a full TeX distribution (e.g. TeX Live) or **GitHub Actions** [`build-pdf.yaml`](.github/workflows/build-pdf.yaml) to build `src/main.pdf`.
- **Optional — Conda + Autogen** (course agent stack): see [`scripts/CONDA_ENVIRONMENT.md`](scripts/CONDA_ENVIRONMENT.md) and [`scripts/course/run-AgentEval.txt`](scripts/course/run-AgentEval.txt) / [`run-nonAgentEval.txt`](scripts/course/run-nonAgentEval.txt).
- **Optional — extras**: `uv sync --extra kb` (Docling course KB), `uv sync --extra nist-loop` (LangGraph judge-prompt loop).

### Environment variables (live evaluation)

Copy [`.env.example`](.env.example) to `.env` and adjust. Typical values:

| Variable | Role |
|----------|------|
| `OPENAI_API_KEY` | Bearer token for chat completions (e.g. `lm-studio` for local servers). |
| `OPENAI_BASE_URL` | Default `http://localhost:1234/v1` (LM Studio). |
| `NIST_EVAL_MODEL` | Model id (default `unrestricted-knowledge-will-not-refuse-15b`). |

Secrets for **GitHub Actions** are documented in [`.github/SECRETS.md`](.github/SECRETS.md).

## Canonical LaTeX entrypoints (Quiz #3 vs legacy IEEE)

| File | Use when |
|------|-----------|
| **`src/main.tex`** | **Primary** course report for Quiz #3 (NIST RMF stress test): inputs `experiment.tex`, `reproducibility.tex`, etc. Build: `cd src && latexmk -pdf main.tex` (or `pdflatex main`). |
| **`src/ieee_journal.tex`** | **Legacy** IEEEtran shell that `\\input{sec/*.tex}` for multi-author **peer-review-style** sections. Still references cryptography figures in places; for homework submission prefer **`main.tex`** unless the instructor asks for the IEEE layout. |

Planning docs: [`PRD.md`](PRD.md), [`todo.json`](todo.json), [`Design.md`](Design.md).

## Clone and install

```bash
git clone <your-fork-or-remote-url>
cd NIST_AI_Trustworthy_Eval
git submodule update --init --recursive   # if you use submodules (agents paths in .env.example)

uv sync
# Optional dependency groups:
uv sync --extra kb
uv sync --extra nist-loop
```

**Conda (rd-agent-mcp + stack)** from repo root:

```bash
conda env create -f environment.yml
conda activate nist-ai-trustworthy-eval
python -c "import rd_agent_mcp.graph.edges; print('rd_agent_mcp OK')"
rd-agent-mcp --help
```

The Python package name is **`rd_agent_mcp`** (underscores). Minimal path without it: **`python scripts/run_nist_llm_evaluation.py`** still works with stdlib + `scripts/` imports.

## Configuration

1. Copy **`.env.example`** → **`.env`** (or export vars in your shell).
2. Start **LM Studio** (or your server) and load the model matching `NIST_EVAL_MODEL`.
3. Course index and paths: **`test_cases/CONFIG`** (`order` q1–q14, `paths.*`, `metadata`).

## Happy path: NIST Quiz #3 evaluation

```bash
python scripts/verify_nist_prompt_inventory.py   # optional: 14 ids, no API
```

Live run (writes `output/results/nist_eval_latest.json`):

```bash
export OPENAI_API_KEY=lm-studio
export OPENAI_BASE_URL=http://localhost:1234/v1
export NIST_EVAL_MODEL=unrestricted-knowledge-will-not-refuse-15b
python scripts/run_nist_llm_evaluation.py
```

Orchestrated refresh (CONFIG-driven; runs the live NIST driver unless `--skip-nist-eval`):

```bash
python scripts/run_coursework_outputs.py
```

After human review, edit **`output/results/nist_quiz_scores.json`**, then:

```bash
python scripts/emit_nist_rubric_table.py
```

## Extended workflows

### LangGraph judge prompts

```bash
uv sync --extra nist-loop
uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py
```

### Course KB (Docling)

```bash
uv sync --extra kb
uv run --extra kb python scripts/extract_course_kb_docling.py
```

### Article section agents

```bash
uv run python scripts/generate_article_section_agents.py
```

See [`test_cases/article_sections/README.md`](test_cases/article_sections/README.md).

### LaTeX PDF

```bash
cd src && latexmk -pdf -interaction=nonstopmode main.tex
```

### CI workflows

- **Research Pipeline** — [`research-pipeline.yaml`](.github/workflows/research-pipeline.yaml).
- **Agent Demo** — [`agent-demo.yaml`](.github/workflows/agent-demo.yaml): phase-1 (self-hosted Ollama), phase-2/3 (cloud); push runs cloud phases when `output/agent_eval/phase1_histories.json` is committed.

### Workflow static check (optional)

To lint workflow YAML locally (separate tool):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)
./actionlint .github/workflows/*.yaml
```

## Where things live

| Area | Purpose |
|------|---------|
| `scripts/` | NIST driver, orchestration, course extractors. |
| `test_cases/rd_agent/q1`–`q14/` | Per-question CONFIG and workflows. |
| `test_cases/CONFIG` | Top-level quiz index. |
| `src/` | LaTeX: **`main.tex`** (report), **`ieee_journal.tex`** (legacy IEEE), **`sec/`** (peer-review blocks). |
| `output/results/` | `nist_eval_latest.json`, `nist_quiz_scores.json`, `nist_rubric_table.tex`. |
| `knowledge_base/` | OpenCode templates, course KB. |
| `agents/rd-agent-mcp/` | MCP / LangGraph package. |

Agent-oriented map: **[`AGENTS.md`](AGENTS.md)**.
