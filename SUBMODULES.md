# Git submodules: `rd-agent` and `adk-ralph`

This template tracks **Microsoft R&D Agent** (`rd-agent`) and **adk-ralph** as Git **submodules** under `agents/`, so your clone pins known-good revisions and CI can set `RD_AGENT_PATH` / `ADK_RALPH_PATH` predictably.

| Path | Remote (see [`.gitmodules`](./.gitmodules)) |
|------|---------------------------------------------|
| `agents/rd-agent` | `https://github.com/sweeden-ttu/rd-agent` |
| `agents/adk-ralph` | `https://github.com/sweeden-ttu/adk-ralph` |

For broader context on how they fit the homework → article → MCP workflow, see the main [README](./README.md).

---

## Initialize submodules (recommended)

From the **repository root**:

```bash
git submodule update --init --recursive
```

After this, `agents/rd-agent` and `agents/adk-ralph` are populated. Do **not** run a plain `git clone` into `agents/` unless you intend to detach from submodule tracking.

---

## Install and build

### rd-agent (Python)

```bash
cd agents/rd-agent
# Use a dedicated env (e.g. conda) per your machine policy, then:
pip install -e .
```

Run tasks from the **rd-agent repo** (or ensure its package is on `PYTHONPATH`). Typical entry points follow upstream docs, e.g.:

```bash
rdagent data_science --task "Your task description"
```

If `rdagent` is not on `PATH`, use the same interpreter you used for `pip install -e .` (often `python -m ...` per that repo’s README).

**Capabilities (typical):** literature review, data-science scenarios, benchmarks, experiment-oriented workflows.

### adk-ralph (Rust)

```bash
cd agents/adk-ralph
cargo build --release
```

```bash
# Example: one-shot codegen task
cargo run --release -- "Your implementation task"

# Interactive mode (if supported by that revision)
cargo run --release -- chat
```

**Capabilities (typical):** multi-step codegen, Rust/Python/TS and other targets, PRD/design artifacts, tests.

---

## Environment variables

Align with [`.env.example`](./.env.example):

```bash
# Paths used by rd-agent-mcp wrappers / coordinator
RD_AGENT_PATH=./agents/rd-agent
ADK_RALPH_PATH=./agents/adk-ralph

# rd-agent ↔ OpenAI-compatible API (e.g. LM Studio)
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LITELLM_OPENAI_API_BASE=http://127.0.0.1:1234/v1
OPENAI_API_BASE=http://127.0.0.1:1234/v1
LITELLM_OPENAI_API_KEY=lm-studio

# adk-ralph ↔ Ollama (example)
OLLAMA_HOST=http://localhost:11434
RALPH_MODEL_PROVIDER=ollama
RALPH_LOCAL_MODEL=granite4:3b
```

**Trusted environments only:** `RD_AGENT_MCP_EXEC_AGENTS=true` allows `rd-agent-mcp` to spawn real subprocesses into these repos instead of simulated stubs.

Optional cloud fallbacks (if you configure them in the agents themselves):

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

---

## Agent routing (high level)

| Task type | Primary | Secondary |
|-----------|---------|-----------|
| Data analysis / survey | rd-agent | adk-ralph |
| Literature-style synthesis | rd-agent | — |
| Code / CLI / implementation | adk-ralph | rd-agent |
| Experiment design | both | — |
| Compile pipeline JSON | rd-agent-mcp (`results` phase or MCP `compile_results`) | — |

---

## Local smoke checks

From repo root (best-effort; skips missing dirs):

```bash
bash mcp/examples/agent-commands.sh
```

---

## Homework-oriented agent configs

Per-question YAML under **`test_cases/rd_agent/q{1,2,3}/agents/`** (`rd-agent-survey.yaml`, `adk-ralph-survey.yaml`) describes tasks for **CS 6343-style** tracks (AES diffusion, ECB/CBC, TLS). They are **specs** for humans/tools; execution still depends on `rd-agent-mcp`, Cursor MCP, or manual runs with the submodule checkouts.

---

## Results compilation

There is **no** standalone `rd-agent-mcp compile-results` CLI in the usual Typer surface. Use one of:

- **MCP:** `compile_results` with `agent_results` from `run_agent_pipeline`, or  
- **CLI:** run the graph phase that produces results, e.g. `rd-agent-mcp run-phase results` (with appropriate prior state / wiring per [rd-agent-mcp](https://github.com/sweeden-ttu/rd-agent-mcp) docs).

Install **rd-agent-mcp** separately (e.g. `pip install -e /path/to/rd-agent-mcp`).

---

## Example combined flow

```bash
# 1. Research / analysis (rd-agent)
cd agents/rd-agent && rdagent data_science --task "Summarize Q1 AES Hamming methodology"

# 2. Tooling (adk-ralph)
cd ../adk-ralph && cargo run --release -- "CLI to export Hamming JSON for plots"

# 3. Validate template test layout
cd ../../..   # repo root
rd-agent-mcp validate-tests --test-dir test_cases
```
