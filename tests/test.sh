#!/bin/bash
# Harbor verifier: checks if the model's move sequence achieves the goal state
# Reads model output from /logs/agent/output.txt
# Expected format:
#   Line 1: orientation tuple, e.g. (Y, R, G)
#   Line 2: space-separated moves, e.g. R U R' U'
# Writes reward to /logs/verifier/reward.txt

set -e

mkdir -p /logs/verifier

AGENT_OUTPUT="/logs/agent/output.txt"
TASK_DIR="/workspace"

if [ ! -f "$AGENT_OUTPUT" ]; then
    echo "0" > /logs/verifier/reward.txt
    echo "No agent output found."
    exit 0
fi

OUTPUT=$(cat "$AGENT_OUTPUT")

python3 "$TASK_DIR/verify.py" --output "$OUTPUT" --task-file "$TASK_DIR/tasks/current_task.json"
