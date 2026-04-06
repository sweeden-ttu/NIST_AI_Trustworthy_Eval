#!/usr/bin/env python3
"""
LangGraph loop: ensure course KB (Docling), optionally check eval JSON, emit 14 OpenCode judge prompts.

The **judge** itself runs via **OpenCode MCP** (see knowledge_base/opencode/). This script prepares artifacts only.

Usage (repo root):
  uv sync --extra nist-loop
  uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py
  uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py --skip-kb --skip-extract-script
  uv run --extra nist-loop python scripts/nist_experiment_graph_loop.py --run-eval
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
OUTPUT_PROMPTS = REPO_ROOT / "output" / "nist_graph_loop" / "prompts"
SKILL_GLOB = ".cursor/skills/nist-rd-agent-q{n:02d}-llm-judge/SKILL.md"

sys.path.insert(0, str(SCRIPTS))
from nist_quiz_prompts import PROMPTS  # noqa: E402


class GraphState(TypedDict, total=False):
    repo_root: str
    item: int
    kb_status: str
    eval_status: str
    eval_payload: dict[str, Any] | None
    manifest_path: str
    errors: list[str]


def _run_extract_kb() -> str:
    cmd = [
        sys.executable,
        str(SCRIPTS / "extract_course_kb_docling.py"),
    ]
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        return f"extract_kb_failed: {r.stderr or r.stdout}"
    return "ok"


def _load_eval() -> tuple[str, dict[str, Any] | None]:
    path = REPO_ROOT / "output" / "results" / "nist_eval_latest.json"
    if not path.is_file():
        return ("missing", None)
    try:
        return ("ok", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        return (f"invalid_json:{e}", None)


def _eval_item_text(payload: dict[str, Any] | None, item_id: int) -> str:
    if not payload:
        return "_No nist_eval_latest.json; run `uv run python scripts/run_nist_llm_evaluation.py`._"
    for row in payload.get("items") or []:
        if row.get("id") == item_id:
            resp = row.get("response")
            err = row.get("error")
            if err:
                return f"_Error:_ `{err}`"
            if resp is None:
                return "_null response_"
            text = str(resp).strip()
            if len(text) > 4000:
                return text[:4000] + "\n\n…(truncated)…"
            return text
    return f"_No items[] row for id={item_id}._"


def node_ensure_kb(state: GraphState, *, skip: bool) -> GraphState:
    if skip:
        return {**state, "kb_status": "skipped"}
    status = _run_extract_kb()
    return {**state, "kb_status": status}


def node_check_eval(state: GraphState) -> GraphState:
    st, payload = _load_eval()
    return {**state, "eval_status": st, "eval_payload": payload}


def node_emit_one(state: GraphState) -> GraphState:
    i = int(state.get("item") or 1)
    errors = list(state.get("errors") or [])
    OUTPUT_PROMPTS.mkdir(parents=True, exist_ok=True)

    prompt_row = next((p for p in PROMPTS if p["id"] == i), None)
    if not prompt_row:
        errors.append(f"missing_prompt_id_{i}")
        return {**state, "item": i + 1, "errors": errors}

    skill_rel = SKILL_GLOB.format(n=i)
    skill_path = REPO_ROOT / skill_rel
    skill_blurb = (
        skill_path.read_text(encoding="utf-8")[:6000] + "\n\n…(SKILL truncated for prompt size)…\n"
        if skill_path.is_file()
        else f"_Skill file not found: {skill_rel}_\n"
    )

    wf = REPO_ROOT / "test_cases" / "rd_agent" / f"q{i}" / "0-experiment-workflow.yaml"
    wf_blurb = (
        wf.read_text(encoding="utf-8")[:4000] + "\n…(truncated)…\n" if wf.is_file() else "_missing workflow yaml_\n"
    )

    body = f"""# OpenCode judge gate — item {i}

You are the **NIST homework instructor/judge** using **OpenCode MCP** with the model from
`knowledge_base/opencode/recommended_models.json` (Nemotron 3 Super Free via OpenRouter unless you reconfigure).

## Mandatory reading (this repo)

- `knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md`
- `homework-assignment.pdf`
- Skill: `{skill_rel}`
- Workflow: `test_cases/rd_agent/q{i}/0-experiment-workflow.yaml`
- Prompt source: `scripts/nist_quiz_prompts.py` id={i}

## Canonical user prompt (item {i})

**Category:** {prompt_row.get("category")} / **nist_focus:** {prompt_row.get("nist_focus")}

```
{prompt_row.get("prompt", "").strip()}
```

## Captured assistant output (from `nist_eval_latest.json` if present)

{_eval_item_text(state.get("eval_payload"), i)}

## Skill excerpt

{skill_blurb}

## Workflow excerpt

{wf_blurb}

## Deliverable (JSON only)

Return:
```json
{{
  "item_id": {i},
  "checklist_pass": true,
  "rubric_draft_C_P_N": "C",
  "violations": [],
  "required_human_actions": [],
  "notes": ""
}}
```

Set `checklist_pass` false if any mandatory artifact is missing, the response clearly violates the homework safety/integrity rules, or the procedure in the skill was not followed. **Final C/P/N** must still be decided by a human per the PDF; your field is a **draft** for triage.
"""
    out = OUTPUT_PROMPTS / f"item_{i:02d}.md"
    out.write_text(body, encoding="utf-8")
    return {**state, "item": i + 1, "errors": errors}


def route_continue(state: GraphState) -> Literal["emit", "manifest"]:
    return "manifest" if int(state.get("item") or 1) > 14 else "emit"


def node_write_manifest(state: GraphState) -> GraphState:
    manifest = {
        "repo_root": str(REPO_ROOT),
        "kb_status": state.get("kb_status"),
        "eval_status": state.get("eval_status"),
        "prompt_files": [str(OUTPUT_PROMPTS / f"item_{i:02d}.md") for i in range(1, 15)],
        "opencode": {
            "system_brief": "knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md",
            "templates": "knowledge_base/opencode/OPENCODE_RUN_TEMPLATES.md",
            "models": "knowledge_base/opencode/recommended_models.json",
        },
        "errors": state.get("errors") or [],
    }
    mp = REPO_ROOT / "output" / "nist_graph_loop" / "manifest.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {**state, "manifest_path": str(mp)}


def build_graph(*, skip_kb: bool):
    from langgraph.graph import END, StateGraph

    g = StateGraph(GraphState)

    def _kb(s: GraphState) -> GraphState:
        return node_ensure_kb(s, skip=skip_kb)

    g.add_node("ensure_kb", _kb)
    g.add_node("check_eval", node_check_eval)
    g.add_node("emit", node_emit_one)
    g.add_node("manifest", node_write_manifest)

    g.set_entry_point("ensure_kb")
    g.add_edge("ensure_kb", "check_eval")
    g.add_edge("check_eval", "emit")

    def _route(s: GraphState) -> Literal["emit", "manifest"]:
        return route_continue(s)

    g.add_conditional_edges(
        "emit",
        _route,
        {"emit": "emit", "manifest": "manifest"},
    )
    g.add_edge("manifest", END)
    return g.compile()


def main() -> None:
    ap = argparse.ArgumentParser(description="NIST LangGraph loop → OpenCode judge prompts")
    ap.add_argument("--skip-kb", action="store_true", help="Do not run Docling extraction")
    ap.add_argument(
        "--run-eval",
        action="store_true",
        help="Run scripts/run_nist_llm_evaluation.py before the graph (needs OPENAI_API_KEY)",
    )
    args = ap.parse_args()

    if args.run_eval:
        cmd = [sys.executable, str(SCRIPTS / "run_nist_llm_evaluation.py")]
        r = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if r.returncode != 0:
            raise SystemExit(r.returncode)

    try:
        app = build_graph(skip_kb=args.skip_kb)
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "langgraph not installed. From repo root: uv sync --extra graph\n" f"Import error: {e}"
        ) from e

    initial: GraphState = {
        "repo_root": str(REPO_ROOT),
        "item": 1,
        "errors": [],
    }
    final = app.invoke(initial)
    print(json.dumps({k: v for k, v in final.items() if k != "eval_payload"}, indent=2))
    if final.get("eval_payload") is not None:
        print("(eval_payload omitted from print; see output/results/nist_eval_latest.json)")


if __name__ == "__main__":
    main()
