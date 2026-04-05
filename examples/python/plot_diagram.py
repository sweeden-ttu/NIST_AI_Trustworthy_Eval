#!/usr/bin/env python3
"""Generate diagrams from results JSON."""

import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt


def plot_results(input_file: str, output_dir: str = "output/diagrams") -> None:
    """Generate plots from results JSON."""

    with open(input_file) as f:
        data = json.load(f)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metrics = data.get("metrics", {})

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f"Results: {data.get('question', 'Unknown')}", fontsize=16)

    # Plot 1: Literature Review Metrics
    if "literature_review" in metrics:
        lr = metrics["literature_review"]
        ax1 = axes[0, 0]
        ax1.bar(
            ["Papers", "Frameworks", "Gaps", "Future"],
            [
                lr.get("papers_analyzed", 0),
                lr.get("frameworks_compared", 0),
                lr.get("gaps_identified", 0),
                lr.get("future_directions", 0),
            ],
            color=["#3498db", "#2ecc71", "#e74c3c", "#9b59b6"],
        )
        ax1.set_title("Literature Review")
        ax1.set_ylabel("Count")

    # Plot 2: Code Generation Metrics
    if "code_generation" in metrics:
        cg = metrics["code_generation"]
        ax2 = axes[0, 1]
        ax2.bar(
            ["Files", "Tests", "LoC"],
            [
                cg.get("files_created", 0),
                cg.get("tests_passed", 0),
                cg.get("lines_of_code", 0) // 100,
            ],
            color=["#1abc9c", "#f39c12", "#e67e22"],
        )
        ax2.set_title("Code Generation")
        ax2.set_ylabel("Count (LoC in 100s)")

    # Plot 3: Evaluation Metrics
    if "evaluation" in metrics:
        ev = metrics["evaluation"]
        ax3 = axes[1, 0]
        labels = ["Accuracy", "F1 Score", "Medal Rate"]
        values = [
            ev.get("accuracy", 0),
            ev.get("f1_score", 0),
            ev.get("any_medal_rate", 0),
        ]
        ax3.bar(labels, values, color=["#3498db", "#2ecc71", "#f39c12"])
        ax3.set_title("Evaluation Metrics")
        ax3.set_ylabel("Score")
        ax3.set_ylim(0, 1)

    # Plot 4: Agent Performance
    ax4 = axes[1, 1]
    ax4.text(
        0.5,
        0.5,
        f"Agent: {data.get('agent_type', 'N/A')}\n"
        f"Status: {data.get('status', 'N/A')}\n"
        f"Timestamp: {data.get('timestamp', 'N/A')}",
        ha="center",
        va="center",
        fontsize=12,
        transform=ax4.transAxes,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )
    ax4.axis("off")

    plt.tight_layout()
    plt.savefig(output_path / "performance.pdf", dpi=300)
    plt.savefig(output_path / "performance.png", dpi=150)

    print(f"Diagrams saved to {output_path}/")


def main():
    parser = argparse.ArgumentParser(description="Generate diagrams from results")
    parser.add_argument(
        "--input", "-i", default="output/results.json", help="Input results JSON file"
    )
    parser.add_argument(
        "--output", "-o", default="output/diagrams", help="Output directory"
    )
    args = parser.parse_args()

    plot_results(args.input, args.output)


if __name__ == "__main__":
    main()
