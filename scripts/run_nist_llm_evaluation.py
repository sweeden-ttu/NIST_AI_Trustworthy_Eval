#!/usr/bin/env python3
"""
Run the 14 NIST-style compliance prompts against an OpenAI-compatible Chat Completions API.

Requires: Python 3.10+
Optional env:
  OPENAI_API_KEY   — bearer token (required for live calls)
  OPENAI_BASE_URL  — default http://localhost:1234/v1 (LM Studio local server)
  NIST_EVAL_MODEL  — model id (default unrestricted-knowledge-will-not-refuse-15b)

Outputs JSON under output/results/ with raw assistant text per item. Rubric labels (C/P/N) are
not inferred automatically; record them after human review (see nist_quiz_scores.json).
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from nist_quiz_prompts import PROMPTS

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "output" / "results"

DEFAULT_OPENAI_BASE_URL = "http://localhost:1234/v1"
DEFAULT_NIST_EVAL_MODEL = "unrestricted-knowledge-will-not-refuse-15b"


def _post_chat_messages(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "messages": messages,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    return str(payload["choices"][0]["message"]["content"])


def _post_chat(
    base_url: str,
    api_key: str,
    model: str,
    user_message: str,
    temperature: float,
    timeout: float,
) -> str:
    return _post_chat_messages(
        base_url,
        api_key,
        model,
        [{"role": "user", "content": user_message}],
        temperature,
        timeout,
    )


def run_eval(
    *,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    delay_s: float,
    timeout: float,
    dry_run: bool,
) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records = []
    prompt_by_id = {row["id"]: row["prompt"] for row in PROMPTS}
    response_after_7: str | None = None

    for row in PROMPTS:
        item = {
            "id": row["id"],
            "category": row["category"],
            "nist_focus": row["nist_focus"],
            "prompt": row["prompt"],
            "response": None,
            "error": None,
        }
        if dry_run:
            item["response"] = "[dry_run: no API call]"
            if row["id"] == 8:
                item["note"] = "Live runs use a 2-turn thread: Item~7 user+assistant, then Item~8 user."
        elif row["id"] == 8 and response_after_7 is not None:
            try:
                messages = [
                    {"role": "user", "content": prompt_by_id[7]},
                    {"role": "assistant", "content": response_after_7},
                    {"role": "user", "content": row["prompt"]},
                ]
                item["response"] = _post_chat_messages(
                    base_url, api_key, model, messages, temperature, timeout
                )
                item["note"] = "2-turn continuation after Item~7 in the same API thread."
            except urllib.error.HTTPError as e:
                item["error"] = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            except Exception as e:  # noqa: BLE001
                item["error"] = repr(e)
            if delay_s > 0:
                time.sleep(delay_s)
        else:
            if row["id"] == 8 and response_after_7 is None:
                item["note"] = "Isolated user turn (Item~7 had no successful response)."
            try:
                item["response"] = _post_chat(
                    base_url, api_key, model, row["prompt"], temperature, timeout
                )
            except urllib.error.HTTPError as e:
                item["error"] = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            except Exception as e:  # noqa: BLE001
                item["error"] = repr(e)
            if delay_s > 0:
                time.sleep(delay_s)
            if row["id"] == 7 and item["error"] is None and item["response"] is not None:
                response_after_7 = item["response"]
        records.append(item)
    return {
        "run_id": run_id,
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "dry_run": dry_run,
        "items": records,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Run NIST Quiz #3 prompt battery via OpenAI-compatible API.")
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT / "nist_eval_latest.json",
        help="Output JSON path (default: output/results/nist_eval_latest.json)",
    )
    p.add_argument("--dry-run", action="store_true", help="Write JSON without calling the API.")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--delay", type=float, default=0.5, help="Seconds between API calls.")
    p.add_argument("--timeout", type=float, default=120.0)
    args = p.parse_args()

    base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("NIST_EVAL_MODEL", DEFAULT_NIST_EVAL_MODEL)

    if not args.dry_run and not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set. Use --dry-run to emit a template JSON, or export the key."
        )

    payload = run_eval(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=args.temperature,
        delay_s=args.delay,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
