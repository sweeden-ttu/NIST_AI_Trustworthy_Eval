# Rag‑V1 homework pipeline (rd-agent-mcp tools)

**Rag‑V1** here means calling **`run_agent_pipeline`** with **`agent_type = "RagV1"`** (alias for **`rd-agent`**). All tools are **named parameters** on the MCP server; set server **`cwd`** to this repo (e.g. `.../rd-ralph-template`) so `homework-assignment.txt` resolves.

**Prerequisites:** LM Studio (or compatible OpenAI base URL) up; `LM_STUDIO_BASE_URL` set if not default; optional `RD_AGENT_PATH` / `ADK_RALPH_PATH` if you run real agents.

---

## Path A — One-shot graph (simplest)

Skips manual chaining; runs the full LangGraph internally (then you can still call **`run_agent_pipeline`** with a fat prompt if you want a separate rd-agent pass).

1. **`list_phases()`** — Confirm phase metadata.
2. **`research_phase`**  
   - `topic`: short label, e.g. `"CS 6343 Homework 1"`  
   - `homework_pdf`: `"homework-assignment.txt"` (or `.pdf` if sidecar `.txt` exists)  
   - `topics`: e.g. `["AES", "ShiftRows", "MixColumns", "ECB", "CBC", "TLS"]`  
   - `papers`: `[]` or paper URLs/ids if you use them  

Stop here if the bundled graph output is enough; otherwise continue with Path B steps 5–6 for embeddings + Rag‑V1.

---

## Path B — Manual tool chain (matches your tool list)

Use this when you want explicit control between steps.

1. **`list_phases()`**

2. **`extract_questions`**  
   - `homework_pdf`: `"homework-assignment.txt"`  
   - `topics`: e.g. `["AES", "ShiftRows", "MixColumns", "modes", "TLS"]`  
   - `papers`: `[]`  
   **Save** the returned list as `questions`.

3. **`design_experiments`**  
   - `questions`: *the list from step 2*  
   - `related_work`: `[]` or strings you care about  
   **Save** the returned list as `experiments` (for prompting).

4. **`create_embeddings`**  
   - `documents`: one string per chunk, e.g. full homework text, each `questions[i].text`, and short strings summarizing each experiment (`test_cases` / raw LLM YAML).  
   - `metadata`: optional parallel list of small dicts (`question_id`, `source`, …).  

5. **`run_agent_pipeline`** (Rag‑V1)  
   - `prompt`: instructions + paste or summarize `questions` and `experiments` (and note that embeddings exist in Chroma for similarity if your agent stack uses them).  
   - `agent_type`: **`"RagV1"`** (same as `rd-agent`)  
   - `language`: `"python"`  
   - `output_dir`: `"./output"`  

   Response includes **`agent_results_item`** for downstream **`compile_results`** (see [mcp-tool-pipeline.md](./mcp-tool-pipeline.md)).

---

## Optional: compile JSON / LaTeX stubs

After **`run_agent_pipeline`**, call **`compile_results`** with:

`agent_results = [ <agent_results_item from the response> ]`

Use `output_format = "json"` or `"latex"` as needed.

---

## Same pipeline from Python (no MCP)

```python
from rd_agent_mcp.functions import run_agent_pipeline

agent_resp = run_agent_pipeline({
    "prompt": "<your full prompt with questions + experiments>",
    "agent_type": "RagV1",
    "language": "python",
    "output_dir": "./output",
})
```

Requires `pip install -e` on **rd-agent-mcp** and a working **rd-agent** install if you expect `success: True`.

---

## Quick reference

| Order | Tool | Role |
|------:|------|------|
| 1 | `list_phases` | Inspect pipeline phases |
| 2 | `research_phase` *or* `extract_questions` | Full graph vs questions only |
| 3 | `design_experiments` | Experiments per question *(Path B)* |
| 4 | `create_embeddings` | Chroma + LM Studio embeddings *(Path B)* |
| 5 | `run_agent_pipeline` (`RagV1`) | rd-agent run with your prompt |
| — | `compile_results` | Optional final bundle |

See also: [mcp-tool-pipeline.md](./mcp-tool-pipeline.md), [research-graph-overview.md](./research-graph-overview.md).
