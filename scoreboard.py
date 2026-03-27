"""
Scoreboard: stacked bar chart comparing model performance.

Each successful run of a task = 0.5 points (so 2/2 runs = 1.0 point).
Bars are broken down by task category (color-coded).

Usage:
    python scoreboard.py                              # default eval_results.json
    python scoreboard.py --results eval_results_v2.json
    python scoreboard.py --save                       # save PNG instead of showing
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


# Task categories and their colors
CATEGORY_MAP = {
    "One-Move": {
        "color": "#4CAF50",  # green
        "tasks": ["task_00a", "task_00b", "task_00c", "task_00d", "task_00e", "task_00f"],
    },
    "Already Solved": {
        "color": "#2196F3",  # blue
        "tasks": ["task_00g"],
    },
    "F2L": {
        "color": "#FF9800",  # orange
        "tasks": ["task_01", "task_04"],
    },
    "OLL": {
        "color": "#9C27B0",  # purple
        "tasks": ["task_02", "task_10", "task_11", "task_12", "task_13"],
    },
    "PLL": {
        "color": "#F44336",  # red
        "tasks": ["task_03", "task_15", "task_16"],
    },
    "Last Layer Combo": {
        "color": "#E91E63",  # pink
        "tasks": ["task_05", "task_14"],
    },
    "Full Scramble": {
        "color": "#795548",  # brown
        "tasks": ["task_17"],
    },
    "Impossible": {
        "color": "#607D8B",  # blue-grey
        "tasks": ["task_06", "task_07", "task_08", "task_09"],
    },
}


def categorize_task(task_id):
    """Return category name for a task ID."""
    for cat, info in CATEGORY_MAP.items():
        for prefix in info["tasks"]:
            if task_id.startswith(prefix):
                return cat
    return "Other"


def compute_scores(results):
    """Compute scores: 0.5 per passing run, grouped by model and category.
    Returns {model: {category: score}}."""
    scores = defaultdict(lambda: defaultdict(float))

    for r in results:
        if r.get("status") in ("dry_run", "api_error"):
            continue
        model = r["model"]
        cat = categorize_task(r["task_id"])
        if r.get("status") == "pass":
            scores[model][cat] += 0.5

    return scores


def compute_max_scores(results):
    """Compute maximum possible score per category (0.5 per run)."""
    # Count total runs per category (across any single model)
    runs_per_cat = defaultdict(int)
    # Use first model found
    models = set()
    for r in results:
        if r.get("status") in ("dry_run",):
            continue
        models.add(r["model"])

    if not models:
        return {}

    first_model = sorted(models)[0]
    for r in results:
        if r.get("status") == "dry_run" or r["model"] != first_model:
            continue
        cat = categorize_task(r["task_id"])
        runs_per_cat[cat] += 1

    return {cat: count * 0.5 for cat, count in runs_per_cat.items()}


def plot_scoreboard(scores, max_scores, save_path=None):
    """Create a stacked bar chart."""
    models = sorted(scores.keys())
    categories = [cat for cat in CATEGORY_MAP.keys() if cat in max_scores]

    if not models or not categories:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(models))
    bar_width = 0.5
    bottoms = np.zeros(len(models))

    for cat in categories:
        values = [scores[m].get(cat, 0) for m in models]
        color = CATEGORY_MAP[cat]["color"]
        max_val = max_scores.get(cat, 0)
        label = f"{cat} (max {max_val:.1f})"
        ax.bar(x, values, bar_width, bottom=bottoms, label=label,
               color=color, edgecolor='white', linewidth=0.5)
        bottoms += values

    # Total score labels on top of bars
    totals = [sum(scores[m].values()) for m in models]
    max_total = sum(max_scores.values())
    for i, (total, model) in enumerate(zip(totals, models)):
        ax.text(i, total + 0.15, f"{total:.1f}/{max_total:.1f}",
                ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11, fontweight='bold')
    ax.set_ylabel("Score (0.5 pts per passing run)", fontsize=11)
    ax.set_title("Rubik's Cube LLM Benchmark — Model Scores", fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.set_ylim(0, max_total + 1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {save_path}")
    else:
        plt.show()


def print_table(scores, max_scores):
    """Print a text summary table."""
    models = sorted(scores.keys())
    categories = [cat for cat in CATEGORY_MAP.keys() if cat in max_scores]

    header = f"{'Category':<20}" + "".join(f"{m:>18}" for m in models) + f"{'Max':>10}"
    print(header)
    print("-" * len(header))

    for cat in categories:
        row = f"{cat:<20}"
        for m in models:
            val = scores[m].get(cat, 0)
            row += f"{val:>18.1f}"
        row += f"{max_scores[cat]:>10.1f}"
        print(row)

    print("-" * len(header))
    totals_row = f"{'TOTAL':<20}"
    max_total = sum(max_scores.values())
    for m in models:
        total = sum(scores[m].values())
        totals_row += f"{total:>18.1f}"
    totals_row += f"{max_total:>10.1f}"
    print(totals_row)


def main():
    parser = argparse.ArgumentParser(description="Model scoreboard with stacked bar chart")
    parser.add_argument("--results", type=str, default="eval_results.json",
                        help="Path to evaluation results JSON")
    parser.add_argument("--save", action="store_true",
                        help="Save PNG to scoreboard.png instead of showing")
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    scores = compute_scores(results)
    max_scores = compute_max_scores(results)

    if not scores:
        print("No results to score.")
        sys.exit(1)

    print_table(scores, max_scores)
    print()

    save_path = "scoreboard.png" if args.save else None
    if args.save:
        matplotlib.use('Agg')
    plot_scoreboard(scores, max_scores, save_path=save_path)


if __name__ == "__main__":
    main()
