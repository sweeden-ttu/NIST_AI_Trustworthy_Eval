#!/usr/bin/env python3
"""
Merge LM Studio model IDs into Cursor IDE's custom model list.

Sources (in order):
  1. GET {LM_STUDIO_BASE_URL}/models — canonical OpenAI-style ids Cursor sends in requests.
  2. lms ls --json --llm — fallback if HTTP fails (disk LLMs; ids usually match the server).

Updates ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb:
  - aiSettings.userAddedModels
  - aiSettings.modelOverrideEnabled
  - openAIBaseUrl, useOpenAIKey

Requires: LM Studio CLI on PATH (~/.lmstudio/bin/lms), Cursor quit recommended to avoid DB locks.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CURSOR_STATE_KEY = (
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser"
)

DEFAULT_BASE = os.environ.get("LM_STUDIO_BASE_URL", "http://192.168.0.13:1234/v1").rstrip("/")
DEFAULT_API_KEY = os.environ.get("LM_STUDIO_API_KEY", "lm-studio")


def _is_embedding_id(model_id: str) -> bool:
    m = model_id.lower()
    return "embedding" in m or m.startswith("text-embedding")


def fetch_models_openai(base_url: str, api_key: str, timeout: float = 10.0) -> list[str]:
    """Return model ids from OpenAI-compatible /v1/models."""
    url = f"{base_url}/models"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"GET {url} failed: {e}") from e
    items = data.get("data") or []
    return [str(x["id"]) for x in items if isinstance(x, dict) and x.get("id")]


def fetch_models_lms_llm() -> list[str]:
    """Return modelKey from `lms ls --json --llm` (local disk LLMs)."""
    try:
        out = subprocess.run(
            ["lms", "ls", "--json", "--llm"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError("lms not found; install LM Studio CLI or add ~/.lmstudio/bin to PATH") from e
    if out.returncode != 0:
        raise RuntimeError(f"lms ls failed: {out.stderr.strip() or out.stdout.strip()}")
    rows = json.loads(out.stdout)
    keys: list[str] = []
    for row in rows:
        if isinstance(row, dict) and row.get("type") == "llm":
            k = row.get("modelKey") or row.get("identifier")
            if k:
                keys.append(str(k))
    return keys


def load_application_user(db_path: Path) -> dict:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT value FROM ItemTable WHERE key = ?",
            (CURSOR_STATE_KEY,),
        ).fetchone()
    finally:
        con.close()
    if not row:
        raise SystemExit(f"Key not found in {db_path}: {CURSOR_STATE_KEY}")
    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    return json.loads(raw)


def save_application_user(db_path: Path, data: dict) -> None:
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "UPDATE ItemTable SET value = ? WHERE key = ?",
            (payload, CURSOR_STATE_KEY),
        )
        if con.total_changes != 1:
            raise RuntimeError("UPDATE did not affect exactly one row")
        con.commit()
    finally:
        con.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help=f"OpenAI-compatible base URL (default: env LM_STUDIO_BASE_URL or {DEFAULT_BASE})",
    )
    p.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help="Bearer token for /v1/models (default: env LM_STUDIO_API_KEY)",
    )
    p.add_argument(
        "--include-embeddings",
        action="store_true",
        help="Also add embedding model ids to Cursor (usually only needed for tooling, not chat).",
    )
    p.add_argument(
        "--lms-fallback-only",
        action="store_true",
        help="Skip HTTP; use only `lms ls --json --llm`.",
    )
    p.add_argument(
        "--union-lms",
        action="store_true",
        help="Union HTTP ids with `lms ls --llm` (covers server down but disk catalog fresh).",
    )
    p.add_argument(
        "--cursor-db",
        type=Path,
        default=Path.home()
        / "Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        help="Path to Cursor state.vscdb",
    )
    p.add_argument("--no-write", action="store_true", help="Print planned changes; do not write DB")
    p.add_argument("--backup", action="store_true", help="Copy state.vscdb to .bak-lmstudio-sync before write")
    args = p.parse_args()
    base = args.base_url.rstrip("/")

    ids: list[str] = []
    source = ""

    if not args.lms_fallback_only:
        try:
            ids = fetch_models_openai(base, args.api_key)
            source = "GET /v1/models"
        except RuntimeError as e:
            print(f"warn: {e}", file=sys.stderr)
            ids = []

    if args.union_lms or not ids:
        try:
            lms_ids = fetch_models_lms_llm()
            if args.union_lms and ids:
                ids = sorted(set(ids) | set(lms_ids))
                source = source + " + lms ls --llm" if source else "lms ls --llm"
            elif not ids:
                ids = lms_ids
                source = "lms ls --llm (fallback)"
        except RuntimeError as e:
            if not ids:
                print(f"error: no models: {e}", file=sys.stderr)
                return 1
            print(f"warn: lms merge skipped: {e}", file=sys.stderr)

    if not args.include_embeddings:
        ids = [i for i in ids if not _is_embedding_id(i)]

    ids = sorted(set(ids))
    if not ids:
        print("error: no model ids after filters", file=sys.stderr)
        return 1

    db_path: Path = args.cursor_db
    if not db_path.is_file():
        print(f"error: Cursor DB not found: {db_path}", file=sys.stderr)
        return 1

    data = load_application_user(db_path)
    ai = data.setdefault("aiSettings", {})
    uam = list(ai.get("userAddedModels") or [])
    moe = list(ai.get("modelOverrideEnabled") or [])

    uam_set = set(uam)
    moe_set = set(moe)
    added_uam = [i for i in ids if i not in uam_set]
    added_moe = [i for i in ids if i not in moe_set]

    for i in ids:
        uam_set.add(i)
        moe_set.add(i)

    ai["userAddedModels"] = sorted(uam_set)
    ai["modelOverrideEnabled"] = sorted(moe_set)
    data["openAIBaseUrl"] = f"{base}/v1" if not base.endswith("/v1") else base
    data["useOpenAIKey"] = True

    print(f"source: {source.strip()}")
    print(f"models ({len(ids)}): {', '.join(ids)}")
    print(f"userAddedModels +{len(added_uam)}: {added_uam or '(none new)'}")
    print(f"modelOverrideEnabled +{len(added_moe)}: {added_moe or '(none new)'}")
    print(f"openAIBaseUrl -> {data['openAIBaseUrl']}")

    if args.no_write:
        print("no-write: skipping DB update")
        return 0

    if args.backup:
        bak = db_path.with_suffix(".vscdb.bak-lmstudio-sync")
        shutil.copy2(db_path, bak)
        print(f"backup: {bak}")

    save_application_user(db_path, data)
    print("ok: updated Cursor state (quit and reopen Cursor if the picker is stale).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
