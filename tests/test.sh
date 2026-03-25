#!/bin/bash
# Harbor verifier: checks if the model's move sequence achieves the goal state
# Reads model output from /logs/agent/output.txt
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

MOVES=$(cat "$AGENT_OUTPUT" | tr -d '\n' | xargs)

python3 "$TASK_DIR/verify.py" --moves "$MOVES" --task-file "$TASK_DIR/tasks/current_task.json"
