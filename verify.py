"""
Verifier script: checks if a move sequence transforms initial_state into goal_state.
Used by tests/test.sh in the Harbor pipeline.

The LLM outputs an orientation tuple (e.g. (Y, R, G)) followed by
space-separated moves. The parser finds the LAST orientation tuple
(to handle reasoning leakage) and supports INVALID and empty-move outputs.
"""

import argparse
import json
import os
import re
import sys

from cube import Cube, verify_solution


def parse_orientation(line):
    """Parse orientation tuple like '(Y, R, G)' from a string.
    Returns (top, front, right) or None if not found."""
    match = re.search(r'\(([A-Z]),\s*([A-Z]),\s*([A-Z])\)', line)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def parse_model_output(raw_output):
    """Parse orientation and moves from model output.
    Finds the LAST orientation tuple (to skip any reasoning/chain-of-thought),
    then reads moves from the line after it.
    Returns (orientation, moves, error_msg)."""
    lines = [l.strip() for l in raw_output.strip().splitlines()]

    # Find the LAST orientation line
    orientation = None
    orient_line_idx = None
    for i, line in enumerate(lines):
        ori = parse_orientation(line)
        if ori:
            orientation = ori
            orient_line_idx = i

    if not orientation:
        return None, None, "Could not find orientation tuple in output"

    # Get everything after the orientation line
    remaining_lines = lines[orient_line_idx + 1:]

    # Check for INVALID response
    for line in remaining_lines:
        cleaned = line.strip()
        if cleaned.startswith("```"):
            continue
        if cleaned.upper() == "INVALID":
            return orientation, "INVALID", None
        break

    # Check if no moves follow (empty = already solved)
    non_empty_remaining = [l for l in remaining_lines if l.strip() and not l.strip().startswith("```")]
    if not non_empty_remaining:
        return orientation, "", None

    # Find moves line (skip empty lines, code fences)
    moves = None
    for line in remaining_lines:
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        if re.search(r"[RLUDFBrludfbxyz]", line):
            moves = re.sub(r'`', '', line).strip()
            break
        break

    if moves is None:
        return orientation, None, "Could not find moves line after orientation"

    return orientation, moves, None


def write_reward(reward, msg=""):
    os.makedirs("/logs/verifier", exist_ok=True)
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write(str(reward))
    if msg:
        print(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default=None,
                        help="Raw LLM output (orientation line + moves line)")
    parser.add_argument("--output-file", type=str, default=None,
                        help="Path to file containing LLM output")
    parser.add_argument("--task-file", type=str, required=True,
                        help="Path to task JSON")
    args = parser.parse_args()

    # Read output from file or argument
    if args.output_file:
        with open(args.output_file, 'r') as f:
            raw_output = f.read()
    elif args.output:
        raw_output = args.output
    else:
        write_reward(0, "FAIL: No output provided (--output or --output-file required)")
        return

    raw_output = raw_output.strip()
    if not raw_output:
        write_reward(0, "FAIL: Empty output")
        return

    with open(args.task_file, 'r') as f:
        task = json.load(f)

    initial_state = task["initial_state"]
    goal_state = task["goal_state"]
    is_impossible = task.get("impossible", False)

    # Parse the model output using hardened parser
    orientation, moves, error = parse_model_output(raw_output)

    if error:
        write_reward(0, f"FAIL: {error}")
        return

    # Handle INVALID responses
    if moves == "INVALID":
        if is_impossible:
            write_reward(1, "PASS: Correctly identified impossible configuration.")
        else:
            write_reward(0, "FAIL: Declared INVALID but task is solvable.")
        return

    # Handle empty moves (already solved)
    if moves == "":
        if initial_state == goal_state:
            write_reward(1, "PASS: Correctly identified already-solved cube.")
        else:
            write_reward(0, "FAIL: No moves provided but cube is not solved.")
        return

    # If task is impossible but model attempted a solution
    if is_impossible:
        write_reward(0, "FAIL: Attempted to solve an impossible configuration (should output INVALID).")
        return

    # Verify the solution
    success, result = verify_solution(initial_state, goal_state, moves,
                                      orientation=orientation)

    if success:
        write_reward(1, "PASS: Move sequence achieves the goal state.")
    else:
        print("FAIL: Move sequence does not achieve the goal state.")
        print(f"Orientation: {orientation}")
        print(f"Moves: {moves}")
        if isinstance(result, str):
            print(f"Error: {result}")
        else:
            print(f"Resulting state:\n{result}")
            print(f"\nExpected goal state:")
            print(Cube(goal_state))
        write_reward(0)


if __name__ == "__main__":
    main()
