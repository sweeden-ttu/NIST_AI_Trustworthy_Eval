#!/usr/bin/env python3
"""Build numeric-consistency hints for LaTeX section JSON vs coursework result JSON.

Reads all ``output/results/latex-sections*.json`` files, flattens numeric-like tokens from
ground-truth JSON under ``output/results/``, and flags tokens appearing in each section
that never occur in that ground-truth string set (heuristic; false positives possible).

Writes ``output/article_iterations/critique/numeric-consistency.json``.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "output/article_iterations/critique/numeric-consistency.json"
DEFAULT_LATEX_GLOB = "latex-sections*.json"
GROUND_TRUTH_REL = [
    "output/results/q1-summary.json",
    "output/results/q3-cipher-summary.json",
    "output/results/q2/openssl_run.json",
]

# LaTeX/command noise to skip as standalone "numbers"
_SKIP_FULL_MATCH = re.compile(
    r"^(?:sec:|eq:|fig:|tab:|ref:|label|section|begin|end|texttt|includegraphics)$",
    re.I,
)


def _iter_json_values(obj: Any) -> Any:
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_json_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_json_values(v)
    else:
        yield obj


def ground_truth_tokens(paths: list[Path]) -> set[str]:
    """Collect human-relevant tokens from JSON values (numbers and digit-heavy strings)."""
    tokens: set[str] = set()
    for p in paths:
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for v in _iter_json_values(data):
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                tokens.add(str(v))
            elif isinstance(v, float):
                if v.is_integer():
                    tokens.add(str(int(v)))
                else:
                    tokens.add(str(v))
            elif isinstance(v, str) and v:
                # hex blocks and plain digit runs from strings
                for m in re.findall(r"\b0x[0-9a-fA-F]+\b", v):
                    tokens.add(m.lower())
                for m in re.findall(r"\b(?:[0-9a-fA-F]{8,})\b", v):
                    if len(m) >= 8 and re.fullmatch(r"[0-9a-fA-F]+", m):
                        tokens.add(m.lower())
                for m in re.findall(r"-?\d+\.?\d*", v):
                    tokens.add(m)
    return tokens


def extract_latex_tokens(text: str) -> set[str]:
    """Heuristic tokens from LaTeX fragment."""
    if not text:
        return set()
    raw = text
    found: set[str] = set()
    for m in re.findall(r"\b0x[0-9a-fA-F]+\b", raw):
        found.add(m.lower())
    for m in re.findall(r"\b[0-9a-fA-F]{16,}\b", raw):
        found.add(m.lower())
    for m in re.findall(r"-?\d+\.?\d*", raw):
        if _SKIP_FULL_MATCH.match(m):
            continue
        found.add(m)
    return found


def load_latex_section_files(results_dir: Path, pattern: str) -> list[Path]:
    return sorted(results_dir.glob(pattern))


def load_q2_json_files(results_dir: Path) -> list[Path]:
    q2 = results_dir / "q2"
    if not q2.is_dir():
        return []
    return sorted(p for p in q2.glob("*.json") if p.is_file())


def _rel_to_root(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p.resolve())


def _unique_gt_paths(results_dir: Path) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for rel in GROUND_TRUTH_REL:
        p = (ROOT / rel).resolve()
        if p.is_file() and p not in seen:
            seen.add(p)
            ordered.append(p)
    for p in load_q2_json_files(results_dir):
        rp = p.resolve()
        if rp.is_file() and rp not in seen:
            seen.add(rp)
            ordered.append(rp)
    return ordered


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=ROOT / "output/results",
        help="Directory containing latex-sections*.json",
    )
    ap.add_argument(
        "--latex-glob",
        default=DEFAULT_LATEX_GLOB,
        help="Glob under results-dir for section JSON files",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output JSON path",
    )
    args = ap.parse_args()

    results_dir: Path = args.results_dir
    latex_files = load_latex_section_files(results_dir, args.latex_glob)

    gt_paths = _unique_gt_paths(results_dir)
    gt = ground_truth_tokens(gt_paths)

    out: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latex_section_files": [_rel_to_root(p) for p in latex_files],
        "ground_truth_files": [_rel_to_root(p) for p in gt_paths],
        "by_file": {},
    }

    for lf in latex_files:
        try:
            sections = json.loads(lf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            out["by_file"][lf.name] = {"error": str(e)}
            continue
        if not isinstance(sections, dict):
            out["by_file"][lf.name] = {"error": "root must be a JSON object"}
            continue

        by_sec: dict[str, Any] = {}
        for key, val in sections.items():
            text = val if isinstance(val, str) else json.dumps(val)
            tokens = extract_latex_tokens(text)
            missing = sorted(t for t in tokens if t not in gt and t.lower() not in gt)
            by_sec[key] = {
                "char_count": len(text),
                "numeric_like_tokens": sorted(tokens),
                "tokens_not_in_ground_truth_union": missing,
            }
        out["by_file"][lf.name] = {"sections": by_sec}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
