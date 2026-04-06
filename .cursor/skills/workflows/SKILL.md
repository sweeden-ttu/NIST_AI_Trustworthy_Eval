---
name: workflows
description: >-
  Surfaces GitHub Actions workflows the user can dispatch and maps the Research
  Pipeline to rd-agent-mcp (CLI or MCP tools). Use when the user types /workflows,
  asks which workflows to run, or wants to mirror research-pipeline locally via MCP.
---

# /workflows — GitHub Actions and Research Pipeline

## When this applies

The user invokes **`/workflows`**, asks what CI workflows exist, how to **dispatch** them, or chooses **Research Pipeline** and wants the **rd-agent-mcp** equivalent (MCP or terminal).

## Step 1: Present workflow menu

From **`.github/workflows/`**, list dispatchable and notable workflows for this repo:

| Workflow file | Name (workflow `name:`) | How it runs | User-facing summary |
|---------------|-------------------------|-------------|---------------------|
| `research-pipeline.yaml` | Research Pipeline | `workflow_dispatch` | Phased rd-agent-mcp research (`phase`, `question`, `provider`); NIST prompt-inventory check; optional test job. |
| `agent-demo.yaml` | Agent Demo | `workflow_dispatch` | Python demo + LaTeX build path; question `all` or `q1`–`q14`. |
| `build-pdf.yaml` | Build LaTeX PDF | `push` / `pull_request` / `workflow_dispatch` | Compiles LaTeX under `src/`; optional debug flag on dispatch. |

Add **one-liner** instructions to dispatch from the repo root (authenticated `gh`):

```bash
gh workflow list
gh workflow run "Research Pipeline" -f phase=full -f question=all -f provider=auto
gh workflow run "Agent Demo" -f question=q1
gh workflow run "Build LaTeX PDF" -f debug_enabled=false
```

Point to [`.github/SECRETS.md`](.github/SECRETS.md) for **OPENAI_API_KEY**, **OPENAI_BASE_URL**, **NIST_EVAL_MODEL**, and other secrets referenced by workflows.

## Step 2: If the user chooses **Research Pipeline**

### 2a — Inputs (match `workflow_dispatch`)

- **`phase`**: `questions` | `experiment` | `embeddings` | `agent` | `results` | `full`
- **`question`**: `all` | `q1` … `q14` (workflow loops when `all` and phase is not `full`)
- **`provider`**: `auto` | `huggingface` | `mistral` | `openai`

### 2b — CI behavior (for accurate advice)

- Installs **`pip install rd-agent-mcp`**.
- **`phase=full`**: runs `rd-agent-mcp research-phase --topic "NIST AI RMF ..."` (see workflow for exact topic string).
- **Otherwise**: `rd-agent-mcp run-phase <phase> --question qN` (or loops over `q1`–`q14` when `question=all`).
- Runs **`python scripts/verify_nist_prompt_inventory.py`** for 14-prompt inventory validation (no API).
- Optional downstream job runs **`python -m rd_agent_mcp.test_runner`** when phase is not `full`.

### 2c — Local parity with **rd-agent-mcp** (MCP: `user-rd-agent-mcp`)

**Before any MCP call:** read the tool descriptor under  
`mcps/user-rd-agent-mcp/tools/<tool_name>.json` (or the repo’s MCP folder) and pass only documented arguments.

**Full graph (equivalent to `phase=full` / `research_phase` tool):**

- Call MCP tool **`research_phase`** with at least **`topic`**; optionally **`homework_pdf`**, **`papers`**, **`topics`**.  
  This matches the LangGraph chain: extract questions → embeddings → design experiments → prompts → agents → compile.

**Per-phase CLI (equivalent to `run-phase <phase>`):** the packaged CLI exposes:

`rd-agent-mcp run-phase questions|experiment|embeddings|agent|results [--question qN]`

Use the terminal when the user wants exact CI parity for a single phase.

### 2d — Semantic task checklist (user vocabulary → MCP)

When the user asks to run **question**, **hypothesis**, **experiment**, **findings**, **update-hypothesis**, or branches **scenario** / **newquestion** / **proposal**, perform **all** relevant steps below in order, carrying **state forward** (paste summaries or structured JSON into the next prompt or `context` object as appropriate).

| Task | Action |
|------|--------|
| **question** | **`extract_questions`**: set `homework_pdf`, `papers`, `topics` per repo (e.g. `homework-assignment.pdf`, NIST topic strings). |
| **hypothesis** | **`run_agent_pipeline`**: `agent_type` **`rd-agent`** or **`adk-ralph`** (or aliases per tool description); **prompt** asks for a testable hypothesis, variables, and predictions using the extracted questions / embeddings context. |
| **experiment** | **`generate_test_cases`**: `question_id` (e.g. `q3`), **`experiment`** object describing design; or run CLI **`run-phase experiment --question qN`**. |
| **findings** | **`run_agent_pipeline`** to synthesize results, then **`compile_results`** with **`agent_results`** set from the pipeline output’s **`agent_results_item`** (per `run_agent_pipeline` / `compile_results` tool docs). Optionally **`answer_question`** for a targeted sub-question with a **`context`** dict built from prior steps. |
| **update-hypothesis** | **`run_agent_pipeline`** again with a prompt that includes the **prior hypothesis** and **new findings**, requesting a revised hypothesis. |
| **scenario** | Treat as **framing**: fold the scenario into **`research_phase.topic`** or the first **`extract_questions`** / **`run_agent_pipeline`** prompt so all later steps stay consistent. |
| **newquestion** | Re-run **`extract_questions`** with updated **`topics`**, or call **`answer_question`** with a new **`sub_question`** and expanded **`context`**. |
| **proposal** | **`run_agent_pipeline`**: prompt for a structured **proposal** (aim, method, milestones); then **`compile_results`** if a single artifact is needed. |

**Embeddings phase (workflow `embeddings`):** use MCP **`create_embeddings`** / **`search_embeddings`** as in tool schemas (`documents`, `query`, optional `phase` / `question_id`).

**Do not invent tool names or parameters**; if a step is unclear, default to **`research_phase`** for an end-to-end run or **`run_phase` CLI** for a single phase matching the workflow.

## Step 3: Optional — LaTeX critique tools

If the user pivots to section-level critique, the same MCP server exposes **`latex_section_critique_*`** tools; read each tool’s JSON schema before calling.

## Anti-patterns

- Do not claim a workflow exists without checking **`.github/workflows/*.yaml`** in the current repo.
- Do not call MCP tools without reading their **descriptor JSON** first.
- Do not store or echo secret values; only reference secret **names** and `.github/SECRETS.md`.
