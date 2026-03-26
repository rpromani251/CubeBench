"""
Verifier script: checks if a move sequence transforms initial_state into goal_state.
Used by tests/test.sh in the Harbor pipeline.

The LLM outputs an orientation tuple on the first line, e.g. (Y, R, G),
followed by space-separated moves on the second line.
Moves are interpreted in the LLM's stated frame of reference.
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True,
                        help="Raw LLM output (orientation line + moves line)")
    parser.add_argument("--task-file", type=str, required=True,
                        help="Path to task JSON")
    args = parser.parse_args()

    with open(args.task_file, 'r') as f:
        task = json.load(f)

    initial_state = task["initial_state"]
    goal_state = task["goal_state"]

    # Parse LLM output: first line = orientation, second line = moves
    lines = [l.strip() for l in args.output.strip().splitlines() if l.strip()]

    if len(lines) < 2:
        print("FAIL: Expected orientation tuple on first line and moves on second line.")
        os.makedirs("/logs/verifier", exist_ok=True)
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("0")
        return

    orientation = parse_orientation(lines[0])
    moves = lines[1]

    if not orientation:
        print(f"FAIL: Could not parse orientation from: {lines[0]}")
        os.makedirs("/logs/verifier", exist_ok=True)
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("0")
        return

    success, result = verify_solution(initial_state, goal_state, moves,
                                      orientation=orientation)

    os.makedirs("/logs/verifier", exist_ok=True)

    if success:
        print("PASS: Move sequence achieves the goal state.")
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("1")
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
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("0")


if __name__ == "__main__":
    main()
