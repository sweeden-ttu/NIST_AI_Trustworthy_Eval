#!/usr/bin/env python3
"""
Regenerate Quiz #3 (NIST trustworthy AI) experiment artifacts per ``test_cases/CONFIG``.

This replaces the legacy toy-crypto Q1–Q3 pipeline. It orchestrates:

1. ``scripts/run_nist_llm_evaluation.py`` — full 14-prompt battery (dry-run or live).
2. ``scripts/emit_nist_rubric_table.py`` — optional, when ``output/results/nist_quiz_scores.json`` exists.

**Dependencies:** stdlib only (plus whatever ``run_nist_llm_evaluation`` needs: urllib, etc.).
No matplotlib / OpenSSL / Pillow required.

Usage (repo root)::

    python scripts/run_coursework_outputs.py              # NIST dry-run + rubric TeX if scores exist
    python scripts/run_coursework_outputs.py --nist-live  # live API (needs OPENAI_API_KEY)
    python scripts/run_coursework_outputs.py --skip-nist-eval  # manifest + rubric only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "test_cases" / "CONFIG"
RESULTS_DIR = REPO_ROOT / "output" / "results"
MANIFEST_PATH = RESULTS_DIR / "experiment_outputs_manifest.json"


def parse_test_cases_config(text: str) -> dict:
    """Parse ``test_cases/CONFIG`` without PyYAML: ``order``, ``metadata``, ``paths``."""
    order: list[str] = []
    paths: dict[str, str] = {}
    metadata: dict[str, str] = {}
    mode: str | None = None
    fold_key: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if line.strip() == "order:":
            mode, fold_key = "order", None
            continue
        if line.strip() == "metadata:":
            mode, fold_key = "metadata", None
            continue
        if line.strip() == "paths:":
            mode, fold_key = "paths", None
            continue
        if line and not line.startswith(" ") and not line.startswith("\t") and line.endswith(":"):
            mode, fold_key = None, None
            continue

        if mode == "order":
            if line.startswith("  - "):
                order.append(line.replace("  - ", "").strip())
            continue

        if mode == "metadata":
            if fold_key and (line.startswith("    ") or line.startswith("\t")):
                chunk = line.strip()
                if chunk:
                    prev = metadata.get(fold_key, "")
                    metadata[fold_key] = f"{prev} {chunk}".strip() if prev else chunk
                continue
            if line.startswith("  ") and ":" in line:
                key, _, val = line.strip().partition(":")
                key = key.strip()
                val = val.strip()
                if val in (">-", "|-"):
                    fold_key = key
                    metadata[key] = ""
                else:
                    fold_key = None
                    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                        val = val[1:-1]
                    metadata[key] = val
            continue

        if mode == "paths":
            if line.startswith("  ") and ":" in line and not line.strip().startswith("#"):
                key, _, val = line.strip().partition(":")
                paths[key.strip()] = val.strip()

    return {"order": order, "paths": paths, "metadata": metadata}


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise SystemExit(f"Missing {CONFIG_PATH}")
    return parse_test_cases_config(CONFIG_PATH.read_text(encoding="utf-8"))


def run_subprocess(argv: list[str], *, cwd: Path) -> int:
    print("+", " ".join(argv), flush=True)
    return subprocess.call(argv, cwd=str(cwd))


def main() -> int:
    p = argparse.ArgumentParser(
        description="Orchestrate NIST Quiz #3 outputs per test_cases/CONFIG (no legacy crypto)."
    )
    p.add_argument(
        "--nist-live",
        action="store_true",
        help="Run live NIST eval (omit --dry-run on the driver). Requires OPENAI_API_KEY unless using a local server that accepts empty key.",
    )
    p.add_argument(
        "--skip-nist-eval",
        action="store_true",
        help="Do not invoke run_nist_llm_evaluation.py.",
    )
    p.add_argument(
        "--nist-out",
        type=Path,
        default=RESULTS_DIR / "nist_eval_latest.json",
        help="Output path for NIST eval JSON (passed to --out on the driver).",
    )
    p.add_argument(
        "--no-emit-rubric-table",
        action="store_true",
        help="Skip emit_nist_rubric_table.py even if nist_quiz_scores.json exists.",
    )
    args = p.parse_args()

    cfg = load_config()
    order = cfg.get("order") or []
    want = [f"q{i}" for i in range(1, 15)]
    if order != want:
        print(
            f"WARNING: test_cases/CONFIG order is {order!r}; expected {want!r}. Continuing.",
            file=sys.stderr,
        )

    paths = cfg.get("paths") or {}
    meta = cfg.get("metadata") if isinstance(cfg.get("metadata"), dict) else {}
    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": str(CONFIG_PATH.relative_to(REPO_ROOT)),
        "metadata_from_config": meta,
        "assignment": meta.get("assignment"),
        "steps": [],
        "paths_from_config": paths,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_nist_eval:
        driver = REPO_ROOT / "scripts" / "run_nist_llm_evaluation.py"
        cmd = [sys.executable, str(driver), "--out", str(args.nist_out)]
        if not args.nist_live:
            cmd.append("--dry-run")
        rc = run_subprocess(cmd, cwd=REPO_ROOT)
        manifest["steps"].append({"name": "run_nist_llm_evaluation", "argv": cmd, "returncode": rc})
        if rc != 0:
            print(f"run_nist_llm_evaluation exited {rc}", file=sys.stderr)
    else:
        manifest["steps"].append({"name": "run_nist_llm_evaluation", "skipped": True})

    scores_path = REPO_ROOT / (paths.get("rubric_json") or "output/results/nist_quiz_scores.json")
    rubric_tex = REPO_ROOT / (paths.get("rubric_table_tex") or "output/results/nist_rubric_table.tex")
    emit_script = REPO_ROOT / "scripts" / "emit_nist_rubric_table.py"

    if not args.no_emit_rubric_table and scores_path.is_file():
        try:
            data = json.loads(scores_path.read_text(encoding="utf-8"))
            scores = data.get("scores")
            if isinstance(scores, dict) and scores:
                cmd = [
                    sys.executable,
                    str(emit_script),
                    "--scores",
                    str(scores_path),
                    "--out",
                    str(rubric_tex),
                ]
                rc = run_subprocess(cmd, cwd=REPO_ROOT)
                manifest["steps"].append({"name": "emit_nist_rubric_table", "argv": cmd, "returncode": rc})
            else:
                manifest["steps"].append(
                    {
                        "name": "emit_nist_rubric_table",
                        "skipped": True,
                        "reason": "nist_quiz_scores.json missing or empty scores object",
                    }
                )
        except (OSError, json.JSONDecodeError) as e:
            manifest["steps"].append(
                {"name": "emit_nist_rubric_table", "skipped": True, "reason": str(e)}
            )
    else:
        manifest["steps"].append(
            {
                "name": "emit_nist_rubric_table",
                "skipped": True,
                "reason": "no scores file or --no-emit-rubric-table",
            }
        )

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
