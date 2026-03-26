"""
Task generator: creates task instances by starting from known states,
applying scrambles, and recording the before/after states.

Workflow:
1. Start from solved cube (in absolute frame: U=Yellow, R=Orange, F=Green, D=White, L=Red, B=Blue)
2. Each task specifies an orientation tuple (top, front, right) for the LLM's frame of reference
3. Oracle moves are written in the LLM's frame; the generator remaps them to absolute for derivation
4. Initial state = solved + inverse of absolute oracle
5. Verify round-trip: initial + oriented oracle = goal
"""

import json
import os
from cube import (
    Cube, SOLVED_STATE, verify_solution,
    get_orientation_map, remap_moves, invert_moves,
    U, R, F, D, L, B,
)


def make_task(task_id, oracle_moves, orientation, description, difficulty, cfop_stage, notes=""):
    """
    Create a task where goal=solved. Oracle moves are in the LLM's frame.
    Derives initial state by applying inverse of the absolute oracle to solved.
    Verifies round-trip with orientation.
    """
    top, front, right = orientation
    face_map = get_orientation_map(top, front, right)

    # Remap oracle to absolute notation
    abs_oracle = remap_moves(oracle_moves, face_map)
    abs_inverse = invert_moves(abs_oracle)

    # Derive initial state
    init_cube = Cube(SOLVED_STATE)
    init_cube.apply_moves(abs_inverse)

    # Verify round-trip via oriented path
    success, result = verify_solution(
        init_cube.state, list(SOLVED_STATE), oracle_moves, orientation=orientation
    )
    if not success:
        raise ValueError(f"Round-trip verification failed for task {task_id}!")

    return {
        "id": task_id,
        "difficulty": difficulty,
        "description": description,
        "orientation": list(orientation),
        "initial_state": init_cube.state,
        "goal_state": list(SOLVED_STATE),
        "oracle_solution": oracle_moves,
        "cfop_stage": cfop_stage,
        "notes": notes,
    }


# ============================================================
# Task definitions
# ============================================================

def generate_all_tasks():
    tasks = []

    # All tasks use orientation (Y, R, G): yellow top, red front, green right
    ORI = ('Y', 'R', 'G')

    # --- Task 0a-0f: One-move solves (easy) ---

    tasks.append(make_task(
        task_id="task_00a_one_move_U",
        oracle_moves="U",
        orientation=ORI,
        description=(
            "The cube is almost solved. The U face is entirely yellow, and the D face is "
            "entirely white. The bottom two layers are solved. However, the top row of each "
            "side face is misaligned: the front face (red center) has blue stickers across "
            "its top row, the right face (green center) has red stickers across its top row, "
            "the back face (orange center) has green stickers across its top row, and the "
            "left face (blue center) has orange stickers across its top row. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: U. Tests basic top-layer spatial reasoning.",
    ))

    tasks.append(make_task(
        task_id="task_00b_one_move_D",
        oracle_moves="D",
        orientation=ORI,
        description=(
            "The cube is almost solved. The U face is entirely yellow, and the D face is "
            "entirely white. The top two layers are solved. However, the bottom row of each "
            "side face is misaligned: the front face (red center) has green stickers across "
            "its bottom row, the right face (green center) has orange stickers across its "
            "bottom row, the back face (orange center) has blue stickers across its bottom "
            "row, and the left face (blue center) has red stickers across its bottom row. "
            "Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: D. Tests basic bottom-layer spatial reasoning.",
    ))

    tasks.append(make_task(
        task_id="task_00c_one_move_F",
        oracle_moves="F",
        orientation=ORI,
        description=(
            "The cube is almost solved. The F face is entirely red, and the B face is "
            "entirely orange. The back two layers are solved. However, the slices adjacent "
            "to the front face are misaligned: the bottom row of the U face has three green "
            "stickers, the left column of the R face has three white stickers, the top row "
            "of the D face has three blue stickers, and the right column of the L face has "
            "three yellow stickers. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: F. Tests front-face spatial reasoning.",
    ))

    tasks.append(make_task(
        task_id="task_00d_one_move_B",
        oracle_moves="B",
        orientation=ORI,
        description=(
            "The cube is almost solved. The F face is entirely red, and the B face is "
            "entirely orange. The front two layers are solved. However, the slices adjacent "
            "to the back face are misaligned: the top row of the U face has three blue "
            "stickers, the right column of the R face has three yellow stickers, the bottom "
            "row of the D face has three green stickers, and the left column of the L face "
            "has three white stickers. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: B. Tests back-face spatial reasoning.",
    ))

    tasks.append(make_task(
        task_id="task_00e_one_move_R",
        oracle_moves="R",
        orientation=ORI,
        description=(
            "The cube is almost solved. The R face is entirely green, and the L face is "
            "entirely blue. The left two layers are solved. However, the slices adjacent "
            "to the right face are misaligned: the right column of the U face has three "
            "orange stickers, the right column of the F face has three yellow stickers, "
            "the right column of the D face has three red stickers, and the left column "
            "of the B face has three white stickers. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: R. Tests right-face spatial reasoning.",
    ))

    tasks.append(make_task(
        task_id="task_00f_one_move_L",
        oracle_moves="L",
        orientation=ORI,
        description=(
            "The cube is almost solved. The R face is entirely green, and the L face is "
            "entirely blue. The right two layers are solved. However, the slices adjacent "
            "to the left face are misaligned: the left column of the U face has three "
            "red stickers, the left column of the F face has three white stickers, "
            "the left column of the D face has three orange stickers, and the right column "
            "of the B face has three yellow stickers. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="One-move solve: L. Tests left-face spatial reasoning.",
    ))

    # --- Task 1: Basic F2L pair insert (easy) ---
    tasks.append(make_task(
        task_id="task_01_f2l_basic_pair_insert",
        oracle_moves="F R' F' R",
        orientation=ORI,
        description=(
            "The white cross is solved on the bottom face. Three out of four F2L pairs "
            "are correctly inserted (front-left, back-left, and back-right slots are solved). "
            "The front-right slot is empty. The white-red-green corner is on the top layer "
            "at UFR with white facing the right face. The red-green edge is at UF with green "
            "facing up. Insert the pair into the front-right slot without disturbing the "
            "other three solved pairs."
        ),
        difficulty="easy",
        cfop_stage="F2L",
        notes="Basic F2L insertion. Green-red pair above the slot.",
    ))

    # --- Task 2: OLL Sune (medium) ---
    tasks.append(make_task(
        task_id="task_02_oll_sune",
        oracle_moves="U2 R U R' U R U2 R'",
        orientation=ORI,
        description=(
            "The first two layers are completely solved. On the top face (U), the center "
            "and all four edges are yellow, but three corners are misoriented: UBL has yellow "
            "on the rear face, UFL has yellow facing the left, and UFR has yellow facing "
            "the front. Only UBR is correctly oriented with yellow on top. Execute a series of moves such that the top face is oriented "
            "with all yellow on top (OLL is done)."
        ),
        difficulty="medium",
        cfop_stage="OLL",
        notes="OLL Sune case. Three corners misoriented, solved by Sune algorithm.",
    ))

    # --- Task 3: PLL T-perm (hard) ---
    tasks.append(make_task(
        task_id="task_03_pll_t_perm",
        oracle_moves="R U R' U' R' F R2 U' R' U' R U R' F'",
        orientation=ORI,
        description=(
            "The entire cube is solved except for the top layer permutation. The top face "
            "is entirely yellow (OLL is done). Two pairs of pieces on the top layer are "
            "swapped: the UL edge and the UR edge need to trade places, and the UFR corner "
            "and the UBR corner need to trade places. Execute a series of moves to solve the cube."
        ),
        difficulty="hard",
        cfop_stage="PLL",
        notes="T-perm PLL case. Two adjacent edge-corner swaps.",
    ))

    # --- Task 4: Double F2L insert (hard) ---

    tasks.append(make_task(
        task_id="task_04_f2l_double_insert",
        oracle_moves="R U' R' U' R U R2 U' R2 U' R'",
        orientation=ORI,
        description=(
            "The white cross is solved on the bottom. Two F2L pairs are solved: back-left "
            "and back-right slots are complete. Two pairs remain unsolved. "
            "On the top layer: the white-red-green corner is at UFR with white facing right, "
            "and the red-green edge is at UB with red facing up. The white-orange-green "
            "corner is at DFR with white facing front, and the orange-green edge is at UF with "
            "orange facing up. Insert both remaining F2L pairs into their correct slots "
            "(front-right and front-left) without disturbing the solved back pairs. Insert "
            "the front-right pair first, then the front-left pair."
        ),
        difficulty="hard",
        cfop_stage="F2L",
        notes="Double F2L insert. Must sequence two inserts with preservation constraint.",
    ))

    # --- Task 5: Full last-layer solve (hard) ---
    tasks.append(make_task(
        task_id="task_05_full_last_layer",
        oracle_moves="L' U2 L U2 R U' L' U R' L",
        orientation=ORI,
        description=(
            "The first two layers are completely solved. The last layer needs both orientation "
            "and permutation. On the U face, we have all edges with yellow facing up: red-yellow in UF," \
            "orange-yellow in UR, green-yellow in UL, and blue-yellow in UB."
            "Then, we have the yellow, blue, and orange corner in UBL, with blue facing up," \
            "the red-blue-yellow corner in UBR with yellow facing right," \
            "the green-orange-yellow corner in UFR with yellow facing the front," \
            "and the green-red-yellow corner in UFL with yellow facing up. Complete the solve by finishing the last layer." 
        ),
        difficulty="hard",
        cfop_stage="OLL+PLL",
        notes="Combined OLL+PLL. Model must solve the last layer given an OLL state",
    ))

    return tasks


def main():
    tasks = generate_all_tasks()

    # Write each task to its difficulty subfolder
    for task in tasks:
        diff = task["difficulty"]
        out_dir = f"tasks/{diff}"
        os.makedirs(out_dir, exist_ok=True)
        path = f"{out_dir}/{task['id']}.json"
        with open(path, 'w') as f:
            json.dump(task, f, indent=2)
        print(f"Generated: {path}")
        print(f"  Stage: {task['cfop_stage']}, Difficulty: {task['difficulty']}")
        print(f"  Oracle: {task['oracle_solution']}")
        print()

    print(f"\nTotal tasks generated: {len(tasks)}")


if __name__ == "__main__":
    main()
