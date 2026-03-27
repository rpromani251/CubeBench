"""
Animated Rubik's Cube evaluation visualizer.

Shows oracle (human) solution side-by-side with model solutions,
stepping through each move one at a time. Exports as GIF or MP4.

Usage:
    # Animate a specific task, oracle vs all models
    python animate_eval.py --task task_04_f2l_double_insert

    # Animate a specific task + specific model
    python animate_eval.py --task task_04_f2l_double_insert --model gpt-5.4

    # Save as GIF (default) or MP4
    python animate_eval.py --task task_04_f2l_double_insert --format mp4

    # Custom results file
    python animate_eval.py --task task_04_f2l_double_insert --results eval_results_v2.json

    # Adjust speed (ms per frame, default 800)
    python animate_eval.py --task task_04_f2l_double_insert --interval 1200
"""

import argparse
import fnmatch
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from cube import Cube, SOLVED_STATE, get_orientation_map, remap_moves
from visualize import render_cube


def compute_trajectory(initial_state, moves_str, orientation=None):
    """Apply moves one at a time, returning a list of (state, move_label) tuples.
    First entry is the initial state with label 'Start'."""
    trajectory = []
    cube = Cube(list(initial_state))
    trajectory.append((list(cube.state), "Start"))

    if not moves_str or moves_str.strip() == "" or moves_str.strip() == "INVALID":
        return trajectory

    # Remap moves if orientation is provided
    if orientation:
        face_map = get_orientation_map(*orientation)
        abs_moves = remap_moves(moves_str, face_map)
    else:
        abs_moves = moves_str

    original_moves = moves_str.split()
    absolute_moves = abs_moves.split()

    for orig_move, abs_move in zip(original_moves, absolute_moves):
        cube.apply_move(abs_move)
        trajectory.append((list(cube.state), orig_move))

    return trajectory


def render_frame(fig, trajectories, frame_idx, labels, task_id):
    """Render one frame: each trajectory at its current step."""
    fig.clear()

    n = len(trajectories)
    for col, (traj, label) in enumerate(zip(trajectories, labels)):
        # Clamp frame index to trajectory length
        idx = min(frame_idx, len(traj) - 1)
        state, move_label = traj[idx]

        ax = fig.add_subplot(1, n, col + 1, projection='3d')
        render_cube(state, title="", ax=ax)

        # Build subtitle
        step_info = f"Step {idx}/{len(traj)-1}"
        if idx == 0:
            move_text = "Initial State"
        elif idx < len(traj):
            # Show the sequence of moves applied so far
            moves_so_far = " ".join(t[1] for t in traj[1:idx+1])
            move_text = f"Last: {move_label}"
        else:
            move_text = "Done"

        # Check if final state matches solved
        is_solved = (state == SOLVED_STATE)
        status = " ✓ SOLVED" if is_solved and idx > 0 else ""

        ax.set_title(f"{label}\n{step_info} | {move_text}{status}",
                     fontsize=10, fontweight='bold')

    fig.suptitle(f"{task_id}  —  Frame {frame_idx}",
                 fontsize=13, fontweight='bold', y=0.98)
    fig.subplots_adjust(wspace=0.05, top=0.88)


def animate_task(task, eval_results, models_filter=None, output_path=None,
                 fmt="gif", interval=800):
    """Create an animated comparison for a single task."""
    task_id = task["id"]
    initial_state = task["initial_state"]
    oracle_moves = task.get("oracle_solution", "")
    orientation = tuple(task.get("orientation", ['Y', 'R', 'G']))

    # Oracle trajectory
    oracle_traj = compute_trajectory(initial_state, oracle_moves, orientation)

    # Model trajectories
    model_trajs = []
    model_labels = []

    # Get relevant eval results for this task
    task_results = [r for r in eval_results if r["task_id"] == task_id]
    if models_filter:
        task_results = [r for r in task_results
                        if any(m.lower() in r["model"].lower() for m in models_filter)]

    # Deduplicate: take the first run per model
    seen_models = set()
    for r in task_results:
        if r["model"] in seen_models:
            continue
        seen_models.add(r["model"])

        moves = r.get("moves", "")
        ori = r.get("orientation")
        if isinstance(ori, list):
            ori = tuple(ori)

        if moves and moves != "INVALID":
            try:
                traj = compute_trajectory(initial_state, moves, ori)
            except Exception as e:
                print(f"  Warning: could not compute trajectory for {r['model']}: {e}")
                continue
        else:
            # Model gave no moves or INVALID — just show initial state
            traj = [(list(initial_state), "Start")]
            if moves == "INVALID":
                traj.append((list(initial_state), "INVALID"))

        status = "PASS" if r.get("status") == "pass" else "FAIL"
        model_labels.append(f"{r['model']}\n[{status}]")
        model_trajs.append(traj)

    if not model_trajs:
        print(f"  No model results found for {task_id}")
        return None

    # Build animation
    all_trajs = [oracle_traj] + model_trajs
    all_labels = [f"Oracle\n(Human)"] + model_labels

    # Total frames = longest trajectory + a few frames pause at the end
    max_steps = max(len(t) for t in all_trajs)
    pause_frames = 3
    total_frames = max_steps + pause_frames

    n_cols = len(all_trajs)
    fig = plt.figure(figsize=(7 * n_cols, 7))

    def update(frame_idx):
        # Clamp to max_steps for pause frames
        effective_idx = min(frame_idx, max_steps - 1)
        render_frame(fig, all_trajs, effective_idx, all_labels, task_id)

    anim = FuncAnimation(fig, update, frames=total_frames, interval=interval)

    # Save
    if output_path is None:
        output_path = f"eval_anim/{task_id}.{fmt}"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"  Rendering {total_frames} frames to {output_path}...")

    if fmt == "gif":
        anim.save(output_path, writer=PillowWriter(fps=max(1, 1000 // interval)))
    elif fmt == "mp4":
        anim.save(output_path, writer='ffmpeg', fps=max(1, 1000 // interval))
    else:
        raise ValueError(f"Unknown format: {fmt}")

    plt.close(fig)
    print(f"  Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Animated Rubik's Cube eval comparison (oracle vs models)")
    parser.add_argument("--task", type=str, required=True,
                        help="Task ID or glob pattern (e.g. task_04*)")
    parser.add_argument("--model", type=str, nargs="+",
                        help="Filter by model name(s)")
    parser.add_argument("--results", type=str, default="eval_results.json",
                        help="Path to evaluation results JSON")
    parser.add_argument("--format", type=str, default="gif", choices=["gif", "mp4"],
                        help="Output format (default: gif)")
    parser.add_argument("--interval", type=int, default=800,
                        help="Milliseconds per frame (default: 800)")
    parser.add_argument("--output", type=str,
                        help="Custom output path (overrides default)")
    args = parser.parse_args()

    # Load eval results
    with open(args.results) as f:
        eval_results = json.load(f)

    # Find matching tasks
    all_task_files = set()
    for r in eval_results:
        if fnmatch.fnmatch(r["task_id"], f"*{args.task}*"):
            all_task_files.add(r["task_file"])

    if not all_task_files:
        # Try loading task directly
        import glob
        matches = glob.glob(f"tasks/*/{args.task}*.json")
        if matches:
            all_task_files = set(matches)
        else:
            print(f"No tasks matching '{args.task}' found in results or task files.")
            sys.exit(1)

    for task_file in sorted(all_task_files):
        with open(task_file) as f:
            task = json.load(f)
        print(f"\nAnimating: {task['id']}")
        animate_task(task, eval_results, models_filter=args.model,
                     output_path=args.output, fmt=args.format,
                     interval=args.interval)


if __name__ == "__main__":
    main()
