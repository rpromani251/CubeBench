"""
Task generator: creates task instances by starting from known states,
applying scrambles, and recording the before/after states.

Workflow:
1. Start from a known partial-solve state (e.g., cross done, 2 F2L pairs done)
2. The goal state is the next CFOP substep completed
3. The initial state is the goal with the inverse of the oracle solution applied
4. Verify round-trip: initial + oracle = goal
"""

import json
import os
from cube import Cube, SOLVED_STATE, verify_solution, U, R, F, D, L, B


def invert_moves(moves_str):
    """Invert a move sequence (reverse order, invert each move)."""
    moves = moves_str.split()
    inverted = []
    for m in reversed(moves):
        if m.endswith("'"):
            inverted.append(m[:-1])
        elif m.endswith("2"):
            inverted.append(m)  # double move is its own inverse
        else:
            inverted.append(m + "'")
    return " ".join(inverted)


def make_task_from_goal(task_id, goal_state, oracle_moves, description, difficulty, cfop_stage, notes=""):
    """
    Given a goal state and an oracle solution, derive the initial state
    by applying the inverse of the oracle moves to the goal.
    Verifies round-trip correctness.
    """
    # Derive initial state: apply inverse moves to goal
    inv_moves = invert_moves(oracle_moves)
    initial_cube = Cube(goal_state)
    initial_cube.apply_moves(inv_moves)
    initial_state = initial_cube.state

    # Verify: initial + oracle = goal
    success, result = verify_solution(initial_state, goal_state, oracle_moves)
    if not success:
        raise ValueError(f"Round-trip verification failed for task {task_id}!")

    task = {
        "id": task_id,
        "difficulty": difficulty,
        "description": description,
        "initial_state": initial_state,
        "goal_state": goal_state,
        "oracle_solution": oracle_moves,
        "cfop_stage": cfop_stage,
        "notes": notes,
    }
    return task


def build_state_with_modifications(base_state, modifications):
    """
    Start from a base state and apply specific sticker overrides.
    modifications: dict of {index: color}
    """
    state = list(base_state)
    for idx, color in modifications.items():
        state[idx] = color
    return state


# ============================================================
# Task definitions
# ============================================================

def generate_all_tasks():
    tasks = []

    # --- Task 1: Basic F2L pair insert ---
    # Start: cross solved on D, two F2L pairs in FR and BL slots.
    # Setup: we take a solved cube, undo one F2L pair, describe the resulting state.
    # Oracle: standard F2L case

    # Goal: cross + 3 F2L pairs (FR, BL, FL solved)
    # We'll construct this by taking solved cube and scrambling only the unsolved portions.

    # Simpler approach: start from solved, apply a known F2L scramble to one slot
    goal_cube = Cube()
    # Scramble only the top layer + the target slot to create a realistic F2L case
    # We'll undo a known F2L algorithm to get the initial state

    # F2L case: corner in UFR with white facing right, edge at UF with green up
    # Standard insert: U R U' R' U' F' U F (basic case 1)
    oracle_1 = "U R U' R' U' F' U F"

    # Start from solved (which represents "cross + all 4 F2L done"), undo the oracle
    # to get initial. But we want only 2 pairs solved initially.
    # Let's do: cross + FR pair + BL pair solved, FL pair needs insertion.
    # After undoing oracle from solved, the FL slot gets disrupted.
    # Actually F2L insert in front-right slot:

    # Let's just use: solved = goal for "all F2L + OLL + PLL done"
    # For a true F2L task, goal = "this pair inserted"
    # Simplest: goal = solved cube (meaning all of first two layers done),
    # initial = solved with one F2L pair ejected

    # Apply inverse of oracle to solved cube to get initial state
    inv_1 = invert_moves(oracle_1)
    init_cube_1 = Cube()
    init_cube_1.apply_moves(inv_1)

    task_1 = {
        "id": "task_01_f2l_basic_insert",
        "difficulty": "medium",
        "description": (
            "The white cross is solved on the bottom face. Three out of four F2L pairs "
            "are correctly inserted (front-left, back-left, and back-right slots are solved). "
            "The front-right slot is empty. The white-red-green corner is on the top layer "
            "at UFR with white facing the right face. The red-green edge is at UF with green "
            "facing up. Pair the corner and edge and insert them into the front-right slot "
            "without disturbing the other three solved pairs."
        ),
        "initial_state": init_cube_1.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_1,
        "cfop_stage": "F2L",
        "notes": "Basic F2L case 1. Corner white-facing-right, edge flipped on top.",
    }

    # Verify
    success, _ = verify_solution(task_1["initial_state"], task_1["goal_state"], oracle_1)
    assert success, "Task 1 verification failed!"
    tasks.append(task_1)

    # --- Task 2: OLL case ---
    # First two layers solved, need to orient last layer
    # OLL case: "T" shape (OLL #33 or similar)
    # Oracle: a known OLL algorithm

    # OLL #33 (T shape): R U R' U' R' F R F'
    oracle_2 = "R U R' U' R' F R F'"

    inv_2 = invert_moves(oracle_2)
    # Goal: F2L done + OLL done (top face all yellow, but PLL not done)
    # Start from: F2L done + top cross done but corners not oriented
    # Actually, let's set goal = top face all yellow (with side stickers potentially permuted)

    # For OLL, goal = all of U face is yellow. Sides may not match.
    # Start from solved, undo OLL alg — this gives us the OLL case.
    # But then the goal is "solved" again which means PLL is also done.
    # That's fine — the model just needs to apply the right OLL alg and it happens to also solve PLL.

    init_cube_2 = Cube()
    init_cube_2.apply_moves(inv_2)

    task_2 = {
        "id": "task_02_oll_t_shape",
        "difficulty": "medium",
        "description": (
            "The first two layers are completely solved. On the top face (U), you see a "
            "'T' shape of yellow: the center is yellow, the UF and UB edges are yellow on top, "
            "and the UL edge is yellow on top, forming a T pointing left. The UR edge has yellow "
            "facing the right side. The UFR and UBR corners have yellow facing the front and back "
            "respectively, not on top. Apply the correct OLL algorithm to orient all top-face "
            "stickers yellow."
        ),
        "initial_state": init_cube_2.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_2,
        "cfop_stage": "OLL",
        "notes": "OLL case. Undoing R U R' U' R' F R F' from solved gives a specific OLL state.",
    }

    success, _ = verify_solution(task_2["initial_state"], task_2["goal_state"], oracle_2)
    assert success, "Task 2 verification failed!"
    tasks.append(task_2)

    # --- Task 3: PLL case ---
    # T-perm: R U R' U' R' F R2 U' R' U' R U R' F'
    oracle_3 = "R U R' U' R' F R2 U' R' U' R U R' F'"

    init_cube_3 = Cube()
    init_cube_3.apply_moves(invert_moves(oracle_3))

    task_3 = {
        "id": "task_03_pll_t_perm",
        "difficulty": "hard",
        "description": (
            "The entire cube is solved except for the top layer permutation. The top face "
            "is entirely yellow (OLL is done). Looking at the top layer sides: the front "
            "has the pattern [green, red, green] (the center headlight matches but the middle "
            "edge is swapped). The right side has [blue, green, blue] — again headlights with "
            "a swapped center edge. This is a T-permutation case. Execute the correct PLL "
            "algorithm to finish the solve."
        ),
        "initial_state": init_cube_3.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_3,
        "cfop_stage": "PLL",
        "notes": "T-perm PLL case. Two adjacent edge-corner swaps.",
    }

    success, _ = verify_solution(task_3["initial_state"], task_3["goal_state"], oracle_3)
    assert success, "Task 3 verification failed!"
    tasks.append(task_3)

    # --- Task 4: Multi-step F2L + constraint preservation ---
    # Two consecutive F2L inserts where the second must preserve the first.
    # Oracle: insert pair 1, then insert pair 2
    oracle_4a = "U R U' R' U' F' U F"  # insert FR slot
    oracle_4b = "U' L' U L U F U' F'"  # insert FL slot
    oracle_4 = oracle_4a + " " + oracle_4b

    init_cube_4 = Cube()
    init_cube_4.apply_moves(invert_moves(oracle_4))

    task_4 = {
        "id": "task_04_f2l_double_insert",
        "difficulty": "hard",
        "description": (
            "The white cross is solved on the bottom. Two F2L pairs are solved: back-left "
            "(orange-blue) and back-right (red-blue) slots are complete. Two pairs remain unsolved. "
            "On the top layer: the white-red-green corner is at UFR with white facing right, and "
            "the red-green edge is at UF with green facing up. The white-orange-green corner is at "
            "UFL with white facing left, and the orange-green edge is at UB with green facing up. "
            "Insert both remaining F2L pairs into their correct slots (front-right and front-left) "
            "without disturbing the solved back pairs. Insert the front-right pair first, then the "
            "front-left pair."
        ),
        "initial_state": init_cube_4.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_4,
        "cfop_stage": "F2L",
        "notes": "Double F2L insert. Must sequence two inserts with preservation constraint.",
    }

    success, _ = verify_solution(task_4["initial_state"], task_4["goal_state"], oracle_4)
    assert success, "Task 4 verification failed!"
    tasks.append(task_4)

    # --- Task 5: Full last-layer solve (OLL + PLL combined) ---
    oracle_5_oll = "R U R' U' R' F R F'"
    oracle_5_pll = "R U R' U' R' F R2 U' R' U' R U R' F'"
    oracle_5 = oracle_5_oll + " " + oracle_5_pll

    init_cube_5 = Cube()
    init_cube_5.apply_moves(invert_moves(oracle_5))

    task_5 = {
        "id": "task_05_full_last_layer",
        "difficulty": "hard",
        "description": (
            "The first two layers are completely solved. The last layer needs both orientation "
            "and permutation. On the U face, the yellow stickers form an incomplete pattern: "
            "center is yellow, the UF, UB, and UL edges show yellow on top but UR has yellow "
            "facing the right side. The UFR corner has yellow facing front, and UBR has yellow "
            "facing back. First orient all last-layer pieces (OLL) so the entire top face is "
            "yellow, then permute them (PLL) to solve the cube completely."
        ),
        "initial_state": init_cube_5.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_5,
        "cfop_stage": "OLL+PLL",
        "notes": "Combined OLL+PLL. Model must recognize both cases and chain them.",
    }

    success, _ = verify_solution(task_5["initial_state"], task_5["goal_state"], oracle_5)
    assert success, "Task 5 verification failed!"
    tasks.append(task_5)

    return tasks


def main():
    tasks = generate_all_tasks()
    os.makedirs("tasks", exist_ok=True)

    for task in tasks:
        path = f"tasks/{task['id']}.json"
        with open(path, 'w') as f:
            json.dump(task, f, indent=2)
        print(f"Generated: {path}")

        # Also print the initial state for visual inspection
        print(f"  Stage: {task['cfop_stage']}, Difficulty: {task['difficulty']}")
        print(f"  Oracle: {task['oracle_solution']}")
        print()

    print(f"\nTotal tasks generated: {len(tasks)}")


if __name__ == "__main__":
    main()
