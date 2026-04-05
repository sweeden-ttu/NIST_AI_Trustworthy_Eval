---
name: rd-agent-mcp-operator
description: Operate rd-agent-mcp (CLI + MCP) from rd-ralph-template with correct cwd, env, homework paths, and links to test_cases and output/.
---

# rd-agent-mcp operator (rd-ralph-template)

## When to use

- Running **rd-agent-mcp** against this repo: phases, MCP tools, or agent submodules under **`agents/rd-agent`** and **`agents/adk-ralph`**.
- After `git submodule update --init --recursive` (see **`SUBMODULES.md`**).

## Environment (repo root)

```bash
# From rd-ralph-template/
export LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
export LM_STUDIO_API_KEY=lm-studio   # optional; matches .env.example
export RD_AGENT_PATH="${RD_AGENT_PATH:-./agents/rd-agent}"
export ADK_RALPH_PATH="${ADK_RALPH_PATH:-./agents/adk-ralph}"
export RD_AGENT_MCP_EXEC_AGENTS=false   # true only in trusted environments
```

Copy **`.env.example`** → **`.env`** and adjust. Chroma persistence used by the server may live under **`chroma_data/`** or paths set in MCP config.

## MCP server

- **cwd:** Set the MCP server working directory to **this repository root** so `homework-assignment.txt`, `test_cases/`, and `output/` resolve.
- **Tools:** Implemented in the **rd-agent-mcp** package (e.g. `server.py`): `list_phases`, `extract_questions`, `design_experiments`, `create_embeddings`, `run_agent_pipeline`, `compile_results`, `research_phase`, `validate_tests`, etc.
- **Examples:** `mcp/examples/mcp-tool-pipeline.md`, `mcp/examples/mcp-tool-payloads.json`, `mcp/examples/rag-v1-homework-pipeline.md` — use **kebab-case** CLI names where shown (`research-phase`, `run-phase`, `validate-tests`).

### Homework path

- Prefer **`homework-assignment.txt`** at repo root (or absolute path). **`mcp-tool-payloads.json`** may reference a PDF; use `.txt` if no PDF is present.

## CLI (install rd-agent-mcp separately)

```bash
pip install -e /path/to/rd-agent-mcp   # or your install

rd-agent-mcp run-phase questions
rd-agent-mcp run-phase experiment
rd-agent-mcp run-phase embeddings
rd-agent-mcp run-phase agent
rd-agent-mcp run-phase results

rd-agent-mcp research-phase --topic "Your topic" --homework-pdf homework-assignment.txt

rd-agent-mcp validate-tests --test-dir test_cases
python -m rd_agent_mcp.test_runner --test-dir test_cases --question q1
```

## Coursework figures + JSON (no MCP required)

Regenerate artifacts consumed by **`src/ieee_journal.tex`**, **`src/main.tex`**, and **`analyze_stats`**:

```bash
conda activate rd-ralph-template
python scripts/run_coursework_outputs.py
```

Outputs: **`output/results/q1-summary.json`**, **`output/results/q2/`**, **`output/results/q3-cipher-summary.json`**, PDFs under **`output/diagrams/`** (see **`skills/homework-to-ieee-article/SKILL.md`** for the full list).

## Real subprocess agents (trusted only)

```bash
export RD_AGENT_MCP_EXEC_AGENTS=true
rd-agent-mcp research-phase --topic "..." --homework-pdf homework-assignment.txt
# or MCP tool research_phase with same parameters
```

Requires working **`rdagent`** / **`cargo`** in the submodule checkouts; see **`mcp/examples/agent-commands.sh`** for smoke checks.

## Routing (high level)

Heavy survey / data-analysis wording → **rd-agent**; implementation / CLI tooling → **adk-ralph**; see **AgentRouter** in rd-agent-mcp for task patterns.

## Related template assets

| Asset | Purpose |
|-------|---------|
| `test_cases/rd_agent/q{1,2,3}/agents/*.yaml` | Homework-oriented agent task specs |
| `test_cases/article_sections/` | Per-`src/sec/*.tex` iteration agents |
| `test_cases/latex_sections_critique/` | Critique `output/results/latex-sections*.json` vs coursework JSON (grades, claims, consistency) |
| `output/results.json` | Demo JSON for `examples/rust/analyze_stats` |
| `output/rust_output.json` | Example Rust CLI output (see `examples/README.md`) |
