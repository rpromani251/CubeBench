"""
Visualize evaluation results: show what each model's moves produced vs the goal.

For each model-task pair, renders three cubes side by side:
  1. Initial state
  2. State after applying the model's moves
  3. Goal state

Usage:
    python visualize_eval.py                              # visualize all results
    python visualize_eval.py --results my_results.json    # custom results file
    python visualize_eval.py --model gpt-5.4              # filter by model
    python visualize_eval.py --task task_01*              # filter by task id
    python visualize_eval.py --save                       # save PNGs instead of showing
"""

import argparse
import fnmatch
import json
import os
import sys

import matplotlib
import matplotlib.pyplot as plt

from cube import Cube, get_orientation_map, remap_moves
from visualize import render_cube


def apply_model_moves(initial_state, orientation, moves):
    """Apply model's moves with its stated orientation, return resulting state."""
    c = Cube(initial_state)
    try:
        if orientation:
            c.apply_moves_oriented(moves, *orientation)
        else:
            c.apply_moves(moves)
        return c.state, None
    except Exception as e:
        return None, str(e)


def render_triplet(initial_state, model_state, goal_state, title, save_path=None):
    """Render initial, model result, and goal side by side."""
    fig = plt.figure(figsize=(20, 7))

    ax1 = fig.add_subplot(131, projection='3d')
    render_cube(initial_state, title="Initial State", ax=ax1)

    ax2 = fig.add_subplot(132, projection='3d')
    if model_state:
        render_cube(model_state, title="Model's Result", ax=ax2)
    else:
        ax2.set_title("Model's Result\n(could not apply moves)")
        ax2.set_xticks([]); ax2.set_yticks([]); ax2.set_zticks([])

    ax3 = fig.add_subplot(133, projection='3d')
    render_cube(goal_state, title="Goal State", ax=ax3)

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize model evaluation results")
    parser.add_argument("--results", type=str, default="eval_results.json",
                        help="Path to evaluation results JSON")
    parser.add_argument("--model", type=str, help="Filter by model name (substring match)")
    parser.add_argument("--task", type=str, help="Filter by task ID (glob match)")
    parser.add_argument("--save", action="store_true",
                        help="Save PNGs to eval_viz/ instead of showing")
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    # Filter
    filtered = results
    if args.model:
        filtered = [r for r in filtered if args.model.lower() in r["model"].lower()]
    if args.task:
        filtered = [r for r in filtered if fnmatch.fnmatch(r["task_id"], f"*{args.task}*")]

    # Skip entries without moves
    visualizable = [r for r in filtered if r.get("moves")]

    if not visualizable:
        print("No results with parseable moves found.")
        if filtered:
            print(f"({len(filtered)} results matched filters but had no moves — "
                  "likely API errors or unparseable output)")
        sys.exit(1)

    print(f"Visualizing {len(visualizable)} result(s)...")

    if args.save:
        os.makedirs("eval_viz", exist_ok=True)
        matplotlib.use('Agg')

    for r in visualizable:
        # Load task data
        with open(r["task_file"]) as f:
            task = json.load(f)

        orientation = r.get("orientation")
        if isinstance(orientation, list):
            orientation = tuple(orientation)
        moves = r["moves"]

        model_state, err = apply_model_moves(task["initial_state"], orientation, moves)

        status = "PASS" if r.get("status") == "pass" else "FAIL"
        title = (f"[{status}] {r['model']} | {r['task_id']} ({r['difficulty']})\n"
                 f"Orientation: {orientation} | Moves: {moves}")

        if err:
            title += f"\nError: {err}"

        if args.save:
            filename = f"eval_viz/{r['model']}_{r['task_id']}.png"
            render_triplet(task["initial_state"], model_state, task["goal_state"],
                           title, save_path=filename)
        else:
            print(f"\n{r['model']} | {r['task_id']} ({status})")
            print(f"  Orientation: {orientation}")
            print(f"  Moves: {moves}")
            render_triplet(task["initial_state"], model_state, task["goal_state"], title)


if __name__ == "__main__":
    main()
