#!/usr/bin/env python3
"""Verify scripts/nist_quiz_prompts.py defines exactly items 1..14 (no API calls)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from nist_quiz_prompts import PROMPTS  # noqa: E402


def main() -> None:
    ids = sorted(p["id"] for p in PROMPTS)
    want = list(range(1, 15))
    if ids != want:
        raise SystemExit(f"expected prompt ids {want}, got {ids}")
    print("OK: 14 NIST prompts in inventory")


if __name__ == "__main__":
    main()
