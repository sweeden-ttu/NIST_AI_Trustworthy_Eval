# OpenCode MCP — copy/paste templates (NIST loop)

Set **`directory`** to the absolute path of **NIST_AI_Trustworthy_Eval** in every call.

Use **`providerID`** / **`modelID`** from [`recommended_models.json`](./recommended_models.json). Confirm with **`opencode_provider_models`** if a call returns empty output.

## 1) Repo context

```json
{
  "tool": "opencode_context",
  "arguments": {
    "directory": "/absolute/path/to/NIST_AI_Trustworthy_Eval"
  }
}
```

## 2) Instructor pass (read rules + KB excerpt)

Replace the prompt body with a short ask to list missing artifacts and contradictions vs `homework-assignment.pdf`.

```json
{
  "tool": "opencode_run",
  "arguments": {
    "directory": "/absolute/path/to/NIST_AI_Trustworthy_Eval",
    "providerID": "openrouter",
    "modelID": "nvidia/nemotron-3-super-120b-a12b:free",
    "maxDurationSeconds": 600,
    "prompt": "You are the NIST homework judge. Read knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md, knowledge_base/course/INDEX.md, and homework-assignment.pdf. List required artifacts and any missing files. JSON only: { \\\"missing\\\": [], \\\"warnings\\\": [], \\\"next_commands\\\": [] }"
  }
}
```

## 3) Per-item gate (repeat for item 1…14)

After `output/nist_graph_loop/prompts/item_XX.md` exists, paste its contents as the user message in **`opencode_reply`** to the same session, or start a new **`opencode_run`** with that file’s body appended.

## 4) Full battery reminder (human or agent shell)

OpenCode may run shell if enabled; otherwise run locally:

```bash
cd /absolute/path/to/NIST_AI_Trustworthy_Eval
uv run python scripts/run_nist_llm_evaluation.py
```
