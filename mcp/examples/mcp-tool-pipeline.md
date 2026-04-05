# rd-agent-mcp: seven-step tool pipeline

MCP tools are **named parameters** (not a single JSON object). Paths are relative to the server **working directory** (set `cwd` in Cursor / LM Studio MCP config).

## 1. List phases

```text
list_phases()
```

## 2. Full graph (optional shortcut)

Runs extract → embeddings → design → prompts → agents → compile internally.

```text
research_phase(
  topic = "AES diffusion and TLS suites",
  homework_pdf = "homework-assignment.txt",
  topics = ["AES", "ECB", "CBC", "TLS"]
)
```

## 3. Extract questions only

```text
extract_questions(
  homework_pdf = "homework-assignment.txt",
  topics = ["AES", "ShiftRows", "MixColumns"],
  papers = []
)
```

Returns a **list** of question objects (`id`, `text`, `sub_questions`, …).

## 4. Design experiments

Pass the **list** from step 3 as `questions`.

```text
design_experiments(
  questions = [ ... ],
  related_work = []
)
```

Returns a **list** of experiment dicts (`question_id`, `test_cases`, `configs`, …).

## 5. Create embeddings

```text
create_embeddings(
  documents = [
    "…homework excerpt…",
    "…paper or topic string…",
    "…experiment design text…"
  ],
  metadata = []
)
```

## 6. Run agent pipeline

Supported `agent_type` values: **`rd-agent`**, **`adk-ralph`**. Aliases: **`RagV1`** / **`rag`** → `rd-agent`; **`ralph`** → `adk-ralph`.

```text
run_agent_pipeline(
  prompt = "Answer the questions using the designed experiments.",
  agent_type = "RagV1",
  language = "python",
  output_dir = "./output"
)
```

The response includes **`agent_results_item`**: a single object shaped for `compile_results`.

## 7. Compile results

Pass a **list** of agent result dicts. Easiest: wrap the item from step 6.

```text
compile_results(
  agent_results = [ <agent_results_item from run_agent_pipeline> ],
  output_format = "json"
)
```

To combine multiple runs, pass `[item1, item2, ...]`.

## Python (dict API, same as MCP)

```python
from rd_agent_mcp.functions import research_phase

resp = research_phase({
    "topic": "AES Round Structure (Homework #1)",
    "papers": [],
    "homework_pdf": "homework-assignment.txt",
    "topics": ["AES", "ShiftRows", "MixColumns"],
})
```

From the **rd-agent-mcp** repo root with `pip install -e .`: `from functions import research_phase`.

## Notes

- **`research_phase`** already runs the whole graph; use steps 3–7 when you want **manual control** between phases.
- **`compile_results`** expects each entry to match `AgentResultModel` (`agent_id`, `agent_type`, `output` as a **dict**, `artifacts`, `status`, `error`). Using `agent_results_item` from `run_agent_pipeline` satisfies this.
- Real subprocess agents: set **`RD_AGENT_MCP_EXEC_AGENTS=true`** (trusted environments only) for LangGraph `run_agents`; `run_agent_pipeline` still invokes local `rd-agent` / `adk-ralph` wrappers when those tools run.
