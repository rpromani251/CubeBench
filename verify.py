"""
Verifier script: checks if a move sequence transforms initial_state into goal_state.
Used by tests/test.sh in the Harbor pipeline.
"""

import argparse
import json
import os
import sys

from cube import Cube, verify_solution


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--moves", type=str, required=True, help="Space-separated move sequence")
    parser.add_argument("--task-file", type=str, required=True, help="Path to task JSON")
    args = parser.parse_args()

    with open(args.task_file, 'r') as f:
        task = json.load(f)

    initial_state = task["initial_state"]
    goal_state = task["goal_state"]

    success, result = verify_solution(initial_state, goal_state, args.moves)

    os.makedirs("/logs/verifier", exist_ok=True)

    if success:
        print("PASS: Move sequence achieves the goal state.")
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("1")
    else:
        print("FAIL: Move sequence does not achieve the goal state.")
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
