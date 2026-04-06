"""Python-callable helpers mirroring MCP tools (dict payloads for scripts/REPL)."""

from __future__ import annotations

import asyncio
import json
from typing import Any


def run_agent_pipeline(params: dict[str, Any]) -> dict[str, Any]:
    """Synchronous entry: same as MCP ``run_agent_pipeline`` with a dict argument.

    ``params`` must include ``prompt`` and ``agent_type``. Optional: ``language``,
    ``output_dir``. ``RagV1`` / ``rag`` map to ``rd-agent``; ``ralph`` → ``adk-ralph``.

    Example::

        from rd_agent_mcp.functions import run_agent_pipeline

        agent_resp = run_agent_pipeline({
            "prompt": "...",
            "agent_type": "RagV1",
            "language": "python",
            "output_dir": "./output",
        })
    """
    return asyncio.run(run_agent_pipeline_async(params))


async def run_agent_pipeline_async(params: dict[str, Any]) -> dict[str, Any]:
    """Async variant for use inside an existing event loop."""
    for key in ("prompt", "agent_type"):
        if key not in params:
            raise KeyError(f"run_agent_pipeline: missing required key {key!r}")
    from rd_agent_mcp.agent_pipeline import execute_agent_pipeline

    return await execute_agent_pipeline(
        prompt=params["prompt"],
        agent_type=params["agent_type"],
        language=params.get("language", "python"),
        output_dir=params.get("output_dir", "./output"),
    )


def research_phase(params: dict[str, Any]) -> dict[str, Any]:
    """Synchronous full research graph; same as MCP ``research_phase`` with a dict body.

    Required: ``topic``. Optional: ``papers``, ``homework_pdf``, ``topics``.

    Example::

        from rd_agent_mcp.functions import research_phase

        resp = research_phase({
            "topic": "AES Round Structure (Homework #1)",
            "papers": [],
            "homework_pdf": "homework-assignment.txt",
            "topics": ["AES", "ShiftRows", "MixColumns"],
        })
    """
    return asyncio.run(research_phase_async(params))


async def research_phase_async(params: dict[str, Any]) -> dict[str, Any]:
    if "topic" not in params:
        raise KeyError("research_phase: missing required key 'topic'")
    from rd_agent_mcp.research_runner import execute_research_phase

    return await execute_research_phase(
        topic=params["topic"],
        papers=params.get("papers"),
        homework_pdf=params.get("homework_pdf"),
        topics=params.get("topics"),
    )


def latex_section_critique_index_ground_truth(params: dict[str, Any]) -> dict[str, Any]:
    """Sync wrapper: ``params`` must include ``project_root``; other keys match ``index_ground_truth``."""
    from rd_agent_mcp.tools import latex_section_critique as lc

    args = dict(params)
    root = args.pop("project_root")
    return lc.index_ground_truth(root, **args)


def latex_section_critique_retrieve_ground_truth(params: dict[str, Any]) -> dict[str, Any]:
    """Sync wrapper: requires ``project_root``; remaining keys passed to ``retrieve_ground_truth``."""
    from rd_agent_mcp.tools import latex_section_critique as lc

    args = dict(params)
    root = args.pop("project_root")
    return lc.retrieve_ground_truth(root, **args)


def latex_section_critique_get_bundle(params: dict[str, Any]) -> dict[str, Any]:
    """Sync wrapper: requires ``project_root``, ``latex_relative_path``, ``section_key``."""
    from rd_agent_mcp.tools import latex_section_critique as lc

    args = dict(params)
    root = args.pop("project_root")
    latex_rel = args.pop("latex_relative_path")
    section_key = args.pop("section_key")
    return lc.get_section_bundle(root, latex_rel, section_key, **args)


def _lc_resolve_task_text(
    project_root: str,
    task_text: str | None,
    agent_yaml_path: str | None,
) -> str:
    from rd_agent_mcp.tools import latex_section_critique as lc

    if task_text:
        return task_text
    if not agent_yaml_path:
        raise ValueError("Provide task_text or agent_yaml_path")
    p = lc.resolve_under_root(project_root, agent_yaml_path)
    return lc.task_from_agent_yaml(p)


def latex_section_critique_build_prompt(params: dict[str, Any]) -> dict[str, Any]:
    """Build one-section critique user message; same keys as MCP ``latex_section_critique_build_prompt``."""
    from rd_agent_mcp.config import Config
    from rd_agent_mcp.tools import latex_section_critique as lc

    cfg = Config.from_env()
    p = dict(params)
    project_root = p.pop("project_root")
    latex_rel = p.pop("latex_relative_path")
    section_key = p.pop("section_key")
    task_text = p.pop("task_text", None)
    agent_yaml_path = p.pop("agent_yaml_path", None)
    gm = p.pop("ground_truth_mode", "truncate")
    if gm not in ("truncate", "rag"):
        raise ValueError('ground_truth_mode must be "truncate" or "rag"')
    p.setdefault("collection_name", lc.DEFAULT_CRITIQUE_COLLECTION)
    if p.get("embedding_model") is None:
        p["embedding_model"] = cfg.embedding_model
    if p.get("embedding_base_url") is None:
        p["embedding_base_url"] = cfg.base_url
    task = _lc_resolve_task_text(project_root, task_text, agent_yaml_path)
    bundle = lc.get_section_bundle(
        project_root,
        latex_rel,
        section_key,
        ground_truth_mode=gm,  # type: ignore[arg-type]
        **p,
    )
    user = lc.build_section_critique_user_message(task, bundle)
    return {
        "user_message": user,
        "approx_bytes": len(user.encode("utf-8")),
    }


async def latex_section_critique_run_section_review_async(
    params: dict[str, Any],
) -> dict[str, Any]:
    from rd_agent_mcp.config import Config
    from rd_agent_mcp.lm_studio.client import LMStudioClient
    from rd_agent_mcp.tools import latex_section_critique as lc

    cfg = Config.from_env()
    p = dict(params)
    temperature = p.pop("temperature", 0.2)
    timeout = p.pop("timeout", 600.0)
    model = p.pop("model", None)
    base_url = p.pop("base_url", None)

    prompt_payload = latex_section_critique_build_prompt(p)
    user = prompt_payload["user_message"]
    client = LMStudioClient(
        model=model or cfg.chat_model,
        base_url=base_url or cfg.base_url,
        api_key=cfg.api_key,
        timeout=timeout,
    )
    try:
        raw = await client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous technical reviewer. Respond with one valid JSON object only; "
                        "no markdown code fences. For a single-section review, return exactly this shape: "
                        '{"grades":{"letter":"B","numeric":85},"claims":[],"consistency_notes":"","action_items":[]}'
                    ),
                },
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    finally:
        await client.close()
    parsed = lc.parse_critique_json_response(raw)
    if isinstance(parsed, dict) and "grades" not in parsed and "section" in parsed:
        parsed = parsed["section"]
    return {"section_critique": parsed, "raw_model_text": raw}


def latex_section_critique_run_section_review(params: dict[str, Any]) -> dict[str, Any]:
    """Sync: run LM Studio for one section (loads ``Config.from_env()``)."""
    return asyncio.run(latex_section_critique_run_section_review_async(params))


def latex_section_critique_merge_partial(params: dict[str, Any]) -> dict[str, Any]:
    """Merge one section into critique JSON; optional ``write_path`` under ``project_root``."""
    from rd_agent_mcp.tools import latex_section_critique as lc

    p = dict(params)
    project_root = p.pop("project_root")
    latex_rel = p.pop("latex_relative_path")
    section_key = p.pop("section_key")
    partial = p.pop("partial_section_critique")
    critique_json_path = p.pop("critique_json_path", None)
    base_critique = p.pop("base_critique", None)
    write_path = p.pop("write_path", None)
    rel_crit = critique_json_path or lc.DEFAULT_CRITIQUE_REL

    if base_critique is not None:
        base = json.loads(json.dumps(base_critique))
    else:
        path = lc.resolve_under_root(project_root, rel_crit)
        if not path.is_file():
            base = {
                "critique_version": 1,
                "inputs": [],
                "ground_truth_paths": [],
                "sections_by_file": {},
                "cross_cutting": {},
            }
        else:
            base = json.loads(path.read_text(encoding="utf-8"))
    merged = lc.merge_section_into_critique(base, latex_rel, section_key, partial)
    if write_path:
        out = lc.resolve_under_root(project_root, write_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


async def latex_section_critique_run_cross_cutting_async(
    params: dict[str, Any],
) -> dict[str, Any]:
    from rd_agent_mcp.config import Config
    from rd_agent_mcp.lm_studio.client import LMStudioClient
    from rd_agent_mcp.tools import latex_section_critique as lc

    cfg = Config.from_env()
    p = dict(params)
    project_root = p.pop("project_root")
    latex_relative_path = p.pop("latex_relative_path")
    task_text = p.pop("task_text", None)
    agent_yaml_path = p.pop("agent_yaml_path", None)
    critique_json_path = p.pop("critique_json_path", None)
    base_critique = p.pop("base_critique", None)
    write_path = p.pop("write_path", None)
    q1_path = p.pop("q1_path", None)
    q2_path = p.pop("q2_path", None)
    q3_path = p.pop("q3_path", None)
    max_digest_chars = p.pop("max_digest_chars", 4000)
    temperature = p.pop("temperature", 0.2)
    timeout = p.pop("timeout", 600.0)
    model = p.pop("model", None)
    base_url = p.pop("base_url", None)
    if p:
        raise TypeError(f"Unexpected keys for run_cross_cutting: {sorted(p)}")

    task = _lc_resolve_task_text(project_root, task_text, agent_yaml_path)
    subset = lc.load_latex_subset_for_cross_cutting(project_root, latex_relative_path)
    gt = lc.load_ground_truth_texts(
        project_root, q1_path=q1_path, q2_path=q2_path, q3_path=q3_path
    )
    user = lc.build_cross_cutting_user_message(
        task, latex_relative_path, subset, gt, max_chars=max_digest_chars
    )
    rel_crit = critique_json_path or lc.DEFAULT_CRITIQUE_REL
    if base_critique is not None:
        base = json.loads(json.dumps(base_critique))
    else:
        path = lc.resolve_under_root(project_root, rel_crit)
        base = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.is_file()
            else {
                "critique_version": 1,
                "inputs": [],
                "ground_truth_paths": [],
                "sections_by_file": {},
                "cross_cutting": {},
            }
        )
    client = LMStudioClient(
        model=model or cfg.chat_model,
        base_url=base_url or cfg.base_url,
        api_key=cfg.api_key,
        timeout=timeout,
    )
    try:
        raw = await client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous technical reviewer. Respond with one valid JSON object only; "
                        'no markdown code fences. Shape: {"cross_cutting":{"results_vs_discussion":"...",'
                        '"results_vs_conclusion":"...","abstract_vs_body":"..."}}'
                    ),
                },
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    finally:
        await client.close()
    parsed = lc.parse_critique_json_response(raw)
    cc = parsed.get("cross_cutting") if isinstance(parsed, dict) else None
    if not isinstance(cc, dict):
        raise ValueError(f"Model did not return cross_cutting dict: {parsed!r}")
    out = dict(base)
    out["cross_cutting"] = cc
    if write_path:
        outp = lc.resolve_under_root(project_root, write_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return {"critique": out, "raw_model_text": raw}


def latex_section_critique_run_cross_cutting(params: dict[str, Any]) -> dict[str, Any]:
    """Sync: refresh ``cross_cutting`` via LM Studio."""
    return asyncio.run(latex_section_critique_run_cross_cutting_async(params))
