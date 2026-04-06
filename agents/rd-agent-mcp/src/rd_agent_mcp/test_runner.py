"""Discover and validate template test_cases layout (YAML + CONFIG)."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def load_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_root_config(test_dir: Path) -> dict:
    cfg = test_dir / "CONFIG"
    if not cfg.is_file():
        raise FileNotFoundError(f"Missing {cfg}")
    data = load_yaml(cfg)
    if not isinstance(data, dict):
        raise ValueError("Root CONFIG must be a mapping")
    if "order" not in data:
        raise ValueError("Root CONFIG must contain 'order'")
    return data


def discover_question_dirs(test_dir: Path, rd_subdir: str = "rd_agent") -> list[Path]:
    root = test_dir / rd_subdir
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir())


def run_validation(test_dir: Path, question: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        meta = validate_root_config(test_dir)
        order = meta.get("order", [])
        if question and question != "all":
            order = [question] if question in order else []
            if not order:
                errors.append(f"Question {question!r} not in root CONFIG order")
                return errors
        for q in order:
            qdir = test_dir / "rd_agent" / q
            if not qdir.is_dir():
                errors.append(f"Missing question dir: {qdir}")
                continue
            qc = qdir / "CONFIG"
            if not qc.is_file():
                errors.append(f"Missing {qc}")
            yamls = list(qdir.glob("*.yaml"))
            if not yamls:
                errors.append(f"No YAML in {qdir}")
            for y in yamls:
                try:
                    load_yaml(y)
                except Exception as e:
                    errors.append(f"Invalid YAML {y}: {e}")
    except Exception as e:
        errors.append(str(e))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate test_cases tree")
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("test_cases"),
        help="Path to test_cases directory",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Validate a single question id (e.g. q1) or omit for all",
    )
    args = parser.parse_args()
    errs = run_validation(args.test_dir.resolve(), question=args.question)
    if errs:
        for e in errs:
            print(e)
        raise SystemExit(1)
    print(f"OK: {args.test_dir}")


if __name__ == "__main__":
    main()
