#!/bin/bash
# Harbor verifier: checks if the model's move sequence achieves the goal state
# Reads model output from /logs/agent/output.txt
# Expected format:
#   Line 1: orientation tuple, e.g. (Y, R, G)
#   Line 2: space-separated moves, e.g. R U R' U'
#   (or INVALID for impossible configurations, or empty for already-solved)
# Writes reward to /logs/verifier/reward.txt

set -e

mkdir -p /logs/verifier

AGENT_OUTPUT="/logs/agent/output.txt"
TASK_DIR="/workspace"
TASK_FILE="${TASK_FILE:-$TASK_DIR/tasks/current_task.json}"

if [ ! -f "$AGENT_OUTPUT" ]; then
    echo "0" > /logs/verifier/reward.txt
    echo "No agent output found."
    exit 0
fi

# Pass output via file to avoid shell escaping issues
python3 "$TASK_DIR/verify.py" --output-file "$AGENT_OUTPUT" --task-file "$TASK_FILE"
