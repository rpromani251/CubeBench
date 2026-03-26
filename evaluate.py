"""
Evaluate frontier LLMs on Rubik's Cube tasks via OpenRouter.

Usage:
    export OPENROUTER_API_KEY="sk-or-..."
    python evaluate.py                           # run all models on all tasks
    python evaluate.py --models claude-opus      # specific model
    python evaluate.py --tasks tasks/easy/*.json # specific tasks
    python evaluate.py --dry-run                 # show prompts without calling API
"""

import argparse
import glob
import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

from cube import Cube, verify_solution

# --- Model registry ---
MODELS = {
    "claude-opus-4.6": "anthropic/claude-opus-4.6",
    "gpt-5.4": "openai/gpt-5.4",
    "gemini-3.1-pro": "google/gemini-3.1-pro-preview",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_prompt_template():
    with open("instruction.md") as f:
        return f.read()


def build_prompt(template, task):
    return template.replace("{{TASK_DESCRIPTION}}", task["description"])


def parse_orientation(line):
    match = re.search(r'\(([A-Z]),\s*([A-Z]),\s*([A-Z])\)', line)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def parse_model_output(raw_output):
    """Parse orientation and moves from model output.
    Tries to be flexible: looks for orientation tuple anywhere, then moves on the next line."""
    lines = [l.strip() for l in raw_output.strip().splitlines() if l.strip()]

    # Find orientation line
    orientation = None
    moves_line_idx = None
    for i, line in enumerate(lines):
        ori = parse_orientation(line)
        if ori:
            orientation = ori
            moves_line_idx = i + 1
            break

    if not orientation:
        return None, None, "Could not find orientation tuple in output"

    # Find moves line (skip empty lines, code fences)
    moves = None
    for i in range(moves_line_idx, len(lines)):
        line = lines[i]
        if line.startswith("```"):
            continue
        # Check if line looks like moves (contains face letters)
        if re.search(r"[RLUDFB]", line):
            # Clean up: remove backticks, extra whitespace
            moves = re.sub(r'`', '', line).strip()
            break

    if not moves:
        return orientation, None, "Could not find moves line after orientation"

    return orientation, moves, None


def call_openrouter(model_id, prompt, api_key):
    """Call OpenRouter API and return the model's response text."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rubiks-cube-llm-benchmark",
        "X-Title": "Rubik's Cube LLM Benchmark",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 512,
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        return None, f"API error: {data['error']}"

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return content, usage


def evaluate_response(task, raw_output):
    """Parse model output and verify against the task. Returns (pass, details)."""
    orientation, moves, parse_err = parse_model_output(raw_output)

    if parse_err:
        return False, {"error": parse_err, "raw_output": raw_output}

    try:
        success, result = verify_solution(
            task["initial_state"], task["goal_state"],
            moves, orientation=orientation
        )
    except Exception as e:
        return False, {
            "error": f"Verification exception: {e}",
            "orientation": orientation,
            "moves": moves,
        }

    details = {
        "orientation": orientation,
        "moves": moves,
        "pass": success,
    }
    if not success and not isinstance(result, str):
        details["resulting_state"] = result
    elif not success:
        details["error"] = result

    return success, details


def run_evaluation(models, task_paths, api_key, dry_run=False, verbose=True):
    template = load_prompt_template()
    results = []

    for task_path in task_paths:
        with open(task_path) as f:
            task = json.load(f)

        prompt = build_prompt(template, task)

        for model_name, model_id in models.items():
            entry = {
                "task_id": task["id"],
                "task_file": task_path,
                "difficulty": task["difficulty"],
                "model": model_name,
                "model_id": model_id,
            }

            if dry_run:
                print(f"\n{'='*60}")
                print(f"[DRY RUN] Model: {model_name} | Task: {task['id']}")
                print(f"{'='*60}")
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                entry["status"] = "dry_run"
                results.append(entry)
                continue

            if verbose:
                print(f"\n{'='*60}")
                print(f"Model: {model_name} | Task: {task['id']} ({task['difficulty']})")
                print(f"{'='*60}")

            try:
                raw_output, usage = call_openrouter(model_id, prompt, api_key)
            except Exception as e:
                print(f"  API call failed: {e}")
                entry["status"] = "api_error"
                entry["error"] = str(e)
                results.append(entry)
                continue

            entry["raw_output"] = raw_output
            entry["usage"] = usage

            if verbose:
                print(f"  Raw output:\n    {raw_output.replace(chr(10), chr(10) + '    ')}")

            passed, details = evaluate_response(task, raw_output)
            entry.update(details)
            entry["status"] = "pass" if passed else "fail"

            if verbose:
                status = "PASS" if passed else "FAIL"
                print(f"  Result: {status}")
                if not passed and "error" in details:
                    print(f"  Error: {details['error']}")
                if passed:
                    print(f"  Oracle: {task.get('oracle_solution', 'N/A')}")
                    print(f"  Model:  {details.get('moves', 'N/A')}")

            results.append(entry)

            # Brief pause between API calls
            time.sleep(1)

    return results


def print_summary(results):
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    # Group by model
    by_model = {}
    for r in results:
        by_model.setdefault(r["model"], []).append(r)

    for model, entries in by_model.items():
        total = len([e for e in entries if e["status"] != "dry_run"])
        passed = len([e for e in entries if e["status"] == "pass"])
        failed = len([e for e in entries if e["status"] == "fail"])
        errors = len([e for e in entries if e["status"] == "api_error"])

        print(f"\n  {model}: {passed}/{total} passed", end="")
        if errors:
            print(f" ({errors} API errors)", end="")
        print()

        for e in entries:
            if e["status"] == "dry_run":
                continue
            icon = "PASS" if e["status"] == "pass" else "FAIL" if e["status"] == "fail" else "ERR "
            print(f"    [{icon}] {e['task_id']} ({e['difficulty']})")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLMs on Rubik's Cube tasks")
    parser.add_argument("--models", nargs="+", choices=list(MODELS.keys()),
                        default=list(MODELS.keys()),
                        help="Models to evaluate")
    parser.add_argument("--tasks", nargs="+",
                        help="Task JSON files (supports globs)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without calling API")
    parser.add_argument("--output", type=str, default="eval_results.json",
                        help="Output file for results")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: OPENROUTER_API_KEY not set.")
        print("Get one at https://openrouter.ai/keys")
        sys.exit(1)

    # Collect task files
    if args.tasks:
        task_paths = []
        for pattern in args.tasks:
            task_paths.extend(glob.glob(pattern))
    else:
        task_paths = sorted(glob.glob("tasks/*/*.json"))

    if not task_paths:
        print("No task files found.")
        sys.exit(1)

    print(f"Evaluating {len(args.models)} models on {len(task_paths)} tasks")
    print(f"Models: {', '.join(args.models)}")
    print(f"Tasks: {', '.join(os.path.basename(p) for p in task_paths)}")

    selected_models = {k: MODELS[k] for k in args.models}
    results = run_evaluation(selected_models, task_paths, api_key,
                             dry_run=args.dry_run)

    print_summary(results)

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to {args.output}")


if __name__ == "__main__":
    main()
