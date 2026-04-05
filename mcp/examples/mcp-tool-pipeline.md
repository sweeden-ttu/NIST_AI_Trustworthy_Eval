# rd-agent-mcp: seven-step tool pipeline (NIST trustworthy evaluation homework)

MCP tools use **named parameters** (not a single JSON object). Paths are relative to the server **working directory** (set `cwd` in Cursor / LM Studio MCP config).

This repo’s graded track is **trustworthy NIST-style LLM evaluation**: fourteen prompts aligned with NIST AI RMF characteristics (`scripts/nist_quiz_prompts.py`), experiment metadata under `test_cases/rd_agent/q1` … `q14`, capture via `scripts/run_nist_llm_evaluation.py`, and rubric labels **C / P / N** per `homework-assignment.pdf`. Use the MCP graph below for **research / experiment design / agents**; use the Python driver for **API capture** of raw assistant text.

## 1. List phases

```text
list_phases()
```

## 2. Full graph (optional shortcut)

Runs extract → embeddings → design → prompts → agents → compile internally.

```text
research_phase(
  topic = "NIST AI RMF trustworthy-characteristics LLM evaluation (14-item battery)",
  homework_pdf = "homework-assignment.pdf",
  topics = [
    "Valid & Reliable",
    "Safe",
    "Secure & Resilient",
    "Explainable & Interpretable",
    "Privacy-Enhanced",
    "Fair bias managed",
    "Accountable Transparent",
    "rubric C P N",
    "test_cases/rd_agent"
  ],
  papers = []
)
```

## 3. Extract questions only

```text
extract_questions(
  homework_pdf = "homework-assignment.pdf",
  topics = [
    "NIST trustworthy AI questionnaire",
    "compliance rubric",
    "prompt injection and jailbreaks",
    "crisis and safety refusals",
    "privacy synthetic PII",
    "fairness harmful demographic claims",
    "accountability training data filtering"
  ],
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

Returns a **list** of experiment dicts (`question_id`, `test_cases`, `configs`, …). Map designs to `test_cases/rd_agent/qN/CONFIG` and `0-experiment-workflow.yaml` where applicable.

## 5. Create embeddings

```text
create_embeddings(
  documents = [
    "…homework excerpt on C/P/N and NIST characteristics…",
    "…rationale for item 1 base-rate reasoning…",
    "…experiment workflow notes for q7–q8 threading…"
  ],
  metadata = []
)
```

## 6. Run agent pipeline

Supported `agent_type` values: **`rd-agent`**, **`adk-ralph`**. Aliases: **`RagV1`** / **`rag`** → `rd-agent`; **`ralph`** → `adk-ralph`.

```text
run_agent_pipeline(
  prompt = "Align experiment write-up and rubric justification with nist_eval_latest.json and homework rubric.",
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

## Capture raw model outputs (repo script, not an MCP tool)

From the **NIST_AI_Trustworthy_Eval** repo root (use **uv**):

```bash
uv run python scripts/run_nist_llm_evaluation.py --dry-run
uv run python scripts/run_nist_llm_evaluation.py
```

Writes `output/results/nist_eval_latest.json`. After human review, record **C / P / N** in `output/results/nist_quiz_scores.json`. Optional LaTeX: `uv run python scripts/emit_nist_rubric_table.py` → `output/results/nist_rubric_table.tex`.

Requires `OPENAI_API_KEY`, and typically `OPENAI_BASE_URL` / `NIST_EVAL_MODEL` for OpenAI-compatible endpoints (e.g. LM Studio). Item **8** uses a **2-turn** thread after item **7** when both succeed.

## Python (dict API, same as MCP)

```python
from rd_agent_mcp.functions import research_phase

resp = research_phase({
    "topic": "NIST trustworthy AI evaluation (Homework Quiz #3)",
    "papers": [],
    "homework_pdf": "homework-assignment.pdf",
    "topics": [
        "Valid Reliable",
        "Safe Secure",
        "Explainable Interpretable",
        "Privacy Fair Accountable",
        "LLM red team",
    ],
})
```

From the **rd-agent-mcp** repo root with `pip install -e .`: `from functions import research_phase`.

## Notes

- **`research_phase`** already runs the whole graph; use steps 3–7 when you want **manual control** between phases.
- **`compile_results`** expects each entry to match `AgentResultModel` (`agent_id`, `agent_type`, `output` as a **dict**, `artifacts`, `status`, `error`). Using `agent_results_item` from `run_agent_pipeline` satisfies this.
- Real subprocess agents: set **`RD_AGENT_MCP_EXEC_AGENTS=true`** (trusted environments only) for LangGraph `run_agents`; `run_agent_pipeline` still invokes local `rd-agent` / `adk-ralph` wrappers when those tools run.
- Article iteration after scores exist: see `test_cases/article_sections/README.md` and `uv run python scripts/generate_article_section_agents.py`.
