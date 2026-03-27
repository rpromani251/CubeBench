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
    Finds the LAST orientation tuple (to skip any reasoning/chain-of-thought),
    then reads moves from the line after it."""
    lines = [l.strip() for l in raw_output.strip().splitlines()]

    # Find the LAST orientation line (models may mention orientation in reasoning)
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

    # Check if the orientation was the last line (or only blank lines follow) — empty moves
    non_empty_remaining = [l for l in remaining_lines if l.strip() and not l.strip().startswith("```")]
    if not non_empty_remaining:
        # No moves line at all — treat as empty moves (already solved)
        return orientation, "", None

    # Find moves line (skip empty lines, code fences)
    moves = None
    for line in remaining_lines:
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        # Check if line looks like moves (contains face letters)
        if re.search(r"[RLUDFBrludfbxyz]", line):
            # Clean up: remove backticks, extra whitespace
            moves = re.sub(r'`', '', line).strip()
            break
        # If the line exists but has no move characters, it might be empty/garbage
        break

    if moves is None:
        # Non-empty line that doesn't look like moves
        return orientation, None, "Could not find moves line after orientation"

    return orientation, moves, None


REASONING_CAP_MODELS = {
    "google/gemini-3.1-pro-preview": 16384,
}


def call_openrouter(model_id, prompt, api_key, temperature=0.0, max_tokens=4096):
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
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Cap reasoning tokens for models that burn excessive hidden thinking
    if model_id in REASONING_CAP_MODELS:
        payload["reasoning"] = {"max_tokens": REASONING_CAP_MODELS[model_id]}

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=300)
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

    # Handle INVALID response
    if moves == "INVALID":
        # Check if the task is actually an impossible permutation
        is_impossible = task.get("impossible", False)
        details = {"orientation": orientation, "moves": moves, "pass": is_impossible}
        if not is_impossible:
            details["error"] = "Model declared INVALID but task is solvable"
        return is_impossible, details

    # Handle empty moves (model says cube is already solved)
    if moves == "":
        # Impossible tasks with empty moves = wrong (should have said INVALID)
        if task.get("impossible", False):
            return False, {
                "error": "Model returned no moves for an impossible task (should have returned INVALID)",
                "orientation": orientation,
                "moves": moves,
            }
        already_solved = (task["initial_state"] == task["goal_state"])
        details = {"orientation": orientation, "moves": moves, "pass": already_solved}
        if not already_solved:
            details["error"] = "Model returned no moves but cube is not solved"
        return already_solved, details

    # If the task is impossible but the model gave moves (didn't say INVALID), it's wrong
    if task.get("impossible", False):
        return False, {
            "error": "Model gave moves for an impossible task (should have returned INVALID)",
            "orientation": orientation,
            "moves": moves,
        }

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


def run_evaluation(models, task_paths, api_key, dry_run=False, verbose=True, runs=1, max_tokens=4096):
    template = load_prompt_template()
    results = []
    # Use temperature > 0 for multiple runs to get variation
    temperature = 0.6 if runs > 1 else 0.0

    for task_path in task_paths:
        with open(task_path) as f:
            task = json.load(f)

        prompt = build_prompt(template, task)

        for model_name, model_id in models.items():
            for run_idx in range(runs):
                entry = {
                    "task_id": task["id"],
                    "task_file": task_path,
                    "difficulty": task["difficulty"],
                    "model": model_name,
                    "model_id": model_id,
                    "run": run_idx + 1,
                }

                if dry_run:
                    if run_idx == 0:  # Only print dry-run once per model/task
                        print(f"\n{'='*60}")
                        print(f"[DRY RUN] Model: {model_name} | Task: {task['id']} | Runs: {runs}")
                        print(f"{'='*60}")
                        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                    entry["status"] = "dry_run"
                    results.append(entry)
                    continue

                run_label = f" (run {run_idx+1}/{runs})" if runs > 1 else ""
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"Model: {model_name} | Task: {task['id']} ({task['difficulty']}){run_label}")
                    print(f"{'='*60}")

                t_start = time.time()
                try:
                    raw_output, usage = call_openrouter(model_id, prompt, api_key, temperature=temperature, max_tokens=max_tokens)
                except Exception as e:
                    elapsed = time.time() - t_start
                    print(f"  API call failed after {elapsed:.1f}s: {e}")
                    entry["status"] = "api_error"
                    entry["error"] = str(e)
                    entry["elapsed_seconds"] = round(elapsed, 2)
                    results.append(entry)
                    continue

                elapsed = time.time() - t_start
                entry["elapsed_seconds"] = round(elapsed, 2)

                if raw_output is None:
                    error_msg = usage if isinstance(usage, str) else "API returned None"
                    if verbose:
                        print(f"  Response time: {elapsed:.1f}s")
                        print(f"  API error: {error_msg}")
                    entry["status"] = "api_error"
                    entry["error"] = error_msg
                    results.append(entry)
                    continue

                entry["raw_output"] = raw_output
                entry["usage"] = usage

                if verbose:
                    print(f"  Response time: {elapsed:.1f}s")
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
    runs = max((r.get("run", 1) for r in results), default=1)
    print(f"\n{'='*60}")
    print(f"SUMMARY (pass@{runs})")
    print(f"{'='*60}")

    # Group by model
    by_model = {}
    for r in results:
        by_model.setdefault(r["model"], []).append(r)

    for model, entries in by_model.items():
        # Group by task for pass@k
        by_task = {}
        for e in entries:
            if e["status"] == "dry_run":
                continue
            by_task.setdefault(e["task_id"], []).append(e)

        tasks_passed = 0
        total_tasks = len(by_task)
        errors = len([e for e in entries if e["status"] == "api_error"])

        print(f"\n  {model}:", end="")

        for task_id in sorted(by_task.keys()):
            task_entries = by_task[task_id]
            any_pass = any(e["status"] == "pass" for e in task_entries)
            if any_pass:
                tasks_passed += 1
            pass_count = sum(1 for e in task_entries if e["status"] == "pass")
            total_runs = len(task_entries)
            icon = "PASS" if any_pass else "FAIL"
            diff = task_entries[0]["difficulty"]
            print(f"\n    [{icon}] {task_id} ({diff}) — {pass_count}/{total_runs} runs passed", end="")

        # Timing stats
        times = [e.get("elapsed_seconds", 0) for e in entries
                 if e.get("elapsed_seconds") is not None and e["status"] != "dry_run"]
        if times:
            avg_time = sum(times) / len(times)
            total_time = sum(times)
            print(f"\n  {model} total: {tasks_passed}/{total_tasks} tasks passed (pass@{runs})"
                  f" | avg {avg_time:.1f}s/call, total {total_time:.1f}s", end="")
        else:
            print(f"\n  {model} total: {tasks_passed}/{total_tasks} tasks passed (pass@{runs})", end="")
        if errors:
            print(f" ({errors} API errors)", end="")
        print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLMs on Rubik's Cube tasks")
    parser.add_argument("--models", nargs="+", choices=list(MODELS.keys()),
                        default=list(MODELS.keys()),
                        help="Models to evaluate")
    parser.add_argument("--tasks", nargs="+",
                        help="Task JSON files (supports globs)")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of runs per model per task (for pass@k)")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="Max output tokens per API call (default: 4096)")
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

    total_calls = len(args.models) * len(task_paths) * args.runs
    print(f"Evaluating {len(args.models)} models on {len(task_paths)} tasks x {args.runs} runs ({total_calls} API calls)")
    print(f"Models: {', '.join(args.models)}")
    print(f"Tasks: {', '.join(os.path.basename(p) for p in task_paths)}")

    selected_models = {k: MODELS[k] for k in args.models}
    results = run_evaluation(selected_models, task_paths, api_key,
                             dry_run=args.dry_run, runs=args.runs,
                             max_tokens=args.max_tokens)

    print_summary(results)

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to {args.output}")


if __name__ == "__main__":
    main()
