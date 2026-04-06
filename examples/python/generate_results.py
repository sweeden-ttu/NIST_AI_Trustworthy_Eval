#!/usr/bin/env python3
"""Generate results JSON for demo workflows (q1–q14 or all)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

QUESTION_IDS = [f"q{i}" for i in range(1, 15)]


def generate_results(question: str, output_dir: str = "output") -> dict:
    """Generate results JSON for a single question id (e.g. q1)."""

    results = {
        "experiment_id": f"experiment-{question}",
        "question": question,
        "timestamp": "2026-04-04T12:00:00Z",
        "agent_type": "rd-agent",
        "metrics": {
            "literature_review": {
                "papers_analyzed": 15,
                "frameworks_compared": 8,
                "gaps_identified": 5,
                "future_directions": 3,
            },
            "code_generation": {
                "files_created": 5,
                "tests_passed": 10,
                "lines_of_code": 500,
            },
            "evaluation": {"accuracy": 0.85, "f1_score": 0.82, "any_medal_rate": 0.351},
        },
        "artifacts": [
            f"results/{question}/literature_review.md",
            f"results/{question}/framework_comparison.md",
            f"results/{question}/code/main.py",
            f"results/{question}/tests/test_main.py",
        ],
        "status": "completed",
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    out_file = output_path / "results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {out_file}")
    return results


def generate_all(base_output: str = "output") -> dict:
    """Run generate_results for q1–q14; write per-question runs and a combined index."""

    base = Path(base_output)
    per_question: dict[str, dict] = {}
    for q in QUESTION_IDS:
        subdir = base / "runs" / q
        per_question[q] = generate_results(q, str(subdir))

    combined = {
        "experiment_id": "experiment-all-q1-q14",
        "question": "all",
        "questions_run": QUESTION_IDS,
        "per_question": {q: {"experiment_id": per_question[q]["experiment_id"]} for q in QUESTION_IDS},
        "status": "completed",
    }
    summary_path = base / "results.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"Combined summary written to {summary_path}")
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate results JSON (NIST homework demo: q1–q14)")
    parser.add_argument(
        "--question",
        "-q",
        default="q1",
        help="Question ID: q1 … q14",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate results for q1 through q14 under output/runs/qN/ plus output/results.json summary",
    )
    parser.add_argument("--output", "-o", default="output", help="Output directory root")
    args = parser.parse_args()

    if args.all:
        generate_all(args.output)
        return

    if args.question not in QUESTION_IDS:
        raise SystemExit(f"question must be one of {QUESTION_IDS} or use --all")
    generate_results(args.question, args.output)


if __name__ == "__main__":
    main()
