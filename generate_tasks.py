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


def make_impossible_task(task_id, orientation, description, difficulty, cfop_stage, notes=""):
    """
    Create an impossible task — one where no solution exists.
    The model should return INVALID.
    """
    return {
        "id": task_id,
        "difficulty": difficulty,
        "description": description,
        "orientation": list(orientation),
        "initial_state": None,  # No meaningful state for impossible tasks
        "goal_state": None,
        "oracle_solution": "INVALID",
        "impossible": True,
        "cfop_stage": cfop_stage,
        "notes": notes,
    }


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

    # Task 00g: Already solved — no moves required
    tasks.append(make_task(
        task_id="task_00g_no_move",
        oracle_moves="",
        orientation=('W', 'B', 'O'),  # Non-standard orientation to test recognition
        description=(
            "You are holding the cube with white on top, blue in front, and orange on the "
            "right. The top face is entirely white. The bottom face is entirely yellow. The "
            "front face is entirely blue. The back face is entirely green. The right face is "
            "entirely orange. The left face is entirely red. Every face is a single uniform "
            "color. Solve the cube."
        ),
        difficulty="easy",
        cfop_stage="n/a",
        notes="Already-solved cube described from non-standard orientation (W, B, O). Tests whether the model recognizes a solved state and returns no moves.",
    ))

    # --- Task 1: Basic F2L pair insert (medium) ---
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
        difficulty="medium",
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

    # --- Tasks 6-9: Impossible permutations ---

    # Task 6: Single twisted corner — violates corner orientation parity (sum must be 0 mod 3)
    tasks.append(make_impossible_task(
        task_id="task_06_impossible_twisted_corner",
        orientation=('Y', 'G', 'O'),
        description=(
            "You are holding the cube with yellow on top, green in front, and orange on the "
            "right. The entire cube is solved except for one corner. The URF corner — the "
            "yellow-green-orange corner — has yellow showing on the front face instead of on "
            "top. All other pieces are in their correct positions and orientations. Reorient "
            "this corner so that yellow faces up to solve the cube."
        ),
        difficulty="impossible",
        cfop_stage="n/a",
        notes="Impossible: single twisted corner violates corner orientation parity (sum of corner twists must be 0 mod 3).",
    ))

    # Task 7: Fake OLL — 2 corners twisted same direction + 1 edge flipped.
    # Violates both corner parity (2 mod 3 ≠ 0) and edge parity (1 mod 2 ≠ 0).
    tasks.append(make_impossible_task(
        task_id="task_07_impossible_fake_oll",
        orientation=('Y', 'O', 'B'),
        description=(
            "You are holding the cube with yellow on top, orange in front, and blue on the "
            "right. The yellow face is fully complete except for the three front pieces. The "
            "UFL corner (the green-orange-yellow corner) has yellow facing the front face. "
            "The UF edge (the yellow-orange edge) has yellow facing the front face. The UFR "
            "corner (the yellow-orange-blue corner) has yellow facing the front face. All "
            "other pieces on the cube are correctly placed and oriented. Reorient these three "
            "pieces so that yellow faces up on all of them to solve the cube."
        ),
        difficulty="impossible",
        cfop_stage="OLL",
        notes="Impossible: 2 corners twisted the same way (sum ≠ 0 mod 3) and 1 edge flipped (sum ≠ 0 mod 2). Violates both parities.",
    ))

    # Task 8: Single 2-edge swap — violates permutation parity (odd edge permutation with even corner permutation).
    tasks.append(make_impossible_task(
        task_id="task_08_impossible_edge_swap",
        orientation=('Y', 'B', 'R'),
        description=(
            "You are holding the cube with yellow on top, blue in front, and red on the "
            "right. The cube is fully solved except for two edges on the top layer. In the "
            "UF position, we have the yellow-green edge with yellow on top and green facing "
            "front. In the UB position, we have the yellow-blue edge with yellow on top and "
            "blue facing back. These two edges need to be swapped — the yellow-blue edge "
            "should be at UF and the yellow-green edge should be at UB. All other pieces are "
            "correctly placed. Swap these two edges to solve the cube."
        ),
        difficulty="impossible",
        cfop_stage="PLL",
        notes="Impossible: a single 2-edge swap is an odd permutation, but corners are identity (even). Permutation parity mismatch.",
    ))

    # Task 9: Impossible orientation — yellow and white are opposite faces and cannot both be visible from adjacent positions.
    tasks.append(make_impossible_task(
        task_id="task_09_impossible_orientation",
        orientation=('Y', 'W', 'G'),
        description=(
            "You are holding the cube with yellow on top, white in front, and green on the "
            "right. All six faces are fully solved — each face is a single uniform color. "
            "Solve the cube."
        ),
        difficulty="impossible",
        cfop_stage="n/a",
        notes="Impossible: yellow (U) and white (D) are opposite faces — they cannot be top and front simultaneously on any valid cube orientation.",
    ))

    # --- Tasks 10-13: OLL cases with varied orientations (medium) ---

    tasks.append(make_task(
        task_id="task_10_oll_edge_corner_mix",
        oracle_moves="L F' L' U' L U F U' L'",
        orientation=('Y', 'B', 'R'),
        description=(
            "You are holding the cube with yellow on top, blue in front, and red on the right. "
            "The first two layers are completely solved. On the top face, yellow appears at the "
            "center, the UBL corner, UBR corner, UFL corner, UL edge, and UR edge. The UF edge "
            "has yellow facing the front (blue) face. The UB edge has yellow facing the back "
            "(green) face. The UFR corner has yellow facing the right (red) face. The UBL corner "
            "has yellow facing the back (green) face. Orient all misoriented pieces so that the "
            "entire top face is yellow."
        ),
        difficulty="medium",
        cfop_stage="OLL",
        notes="OLL with 2 flipped edges and 2 twisted corners. Non-standard orientation (Y, B, R).",
    ))

    tasks.append(make_task(
        task_id="task_11_oll_all_corners",
        oracle_moves="R U2 R2 U' R2 U' R2 U2 R",
        orientation=ORI,
        description=(
            "The first two layers are completely solved. On the top face, the yellow cross is "
            "complete — all four edges (UF, UR, UB, UL) have yellow facing up. However, all four "
            "corners are misoriented: the UFL corner has yellow facing the left (blue) face, the "
            "UFR corner has yellow facing the front (red) face, the UBR corner has yellow facing "
            "the back (orange) face, and the UBL corner also has yellow facing the left (blue) "
            "face. Orient all four corners so that yellow faces up to complete OLL."
        ),
        difficulty="medium",
        cfop_stage="OLL",
        notes="OLL with cross complete but all 4 corners misoriented. Standard orientation.",
    ))

    tasks.append(make_task(
        task_id="task_12_oll_antisune",
        oracle_moves="R U2 R' U' R U' R'",
        orientation=('Y', 'G', 'O'),
        description=(
            "You are holding the cube with yellow on top, green in front, and orange on the "
            "right. The first two layers are completely solved. On the top face, the yellow cross "
            "is complete — all four edges have yellow facing up. Three corners are misoriented: "
            "the UFL corner has yellow facing the front (green) face, the UFR corner has yellow "
            "facing the right (orange) face, and the UBL corner has yellow facing the left (red) "
            "face. Only the UBR corner has yellow correctly on top. Orient the three misoriented "
            "corners so that the entire top face is yellow."
        ),
        difficulty="medium",
        cfop_stage="OLL",
        notes="Anti-Sune OLL case. 3 corners misoriented. Orientation (Y, G, O).",
    ))

    tasks.append(make_task(
        task_id="task_13_oll_t_shape",
        oracle_moves="R U R' U' R' F R2 U R' U' F'",
        orientation=('Y', 'O', 'B'),
        description=(
            "You are holding the cube with yellow on top, orange in front, and blue on the "
            "right. The first two layers are completely solved. On the top face, two edges are "
            "correctly oriented: UB and UL have yellow on top. The UF edge has yellow facing the "
            "front (orange) face, and the UR edge has yellow facing the right (blue) face. Only "
            "the UFR corner has yellow on top. The UFL corner has yellow facing the front (orange) "
            "face, the UBR corner has yellow facing the back (red) face, and the UBL corner has "
            "yellow facing the left (green) face. Orient all misoriented pieces so that the entire "
            "top face is yellow."
        ),
        difficulty="medium",
        cfop_stage="OLL",
        notes="OLL T-shape case. 2 flipped edges, 3 twisted corners. Orientation (Y, O, B).",
    ))

    # --- Tasks 14-16: PLL cases (medium) ---

    tasks.append(make_task(
        task_id="task_14_last_layer_combo",
        oracle_moves="R2 F R U R' F' R U2 R' U2 R",
        orientation=ORI,
        description=(
            "The first two layers are completely solved. On the top face, yellow appears only "
            "at the UBL corner, UBR corner, UL edge, and center. Red stickers face up at UB, "
            "UR, UF, and UFR. The UFL corner has green facing up. On the side faces: the right "
            "face (green center) top row is entirely green. The front face (red center) shows "
            "orange at UFL, blue at UF, and white at UFR. The back face (orange center) shows "
            "orange at UBR, yellow at UB, and orange at UBL. The left face (blue center) shows "
            "blue at UBL, orange at UL, and white at UFL. Solve the cube."
        ),
        difficulty="medium",
        cfop_stage="OLL+PLL",
        notes="Combined last-layer solve. Standard orientation.",
    ))

    tasks.append(make_task(
        task_id="task_15_pll_diagonal_swap",
        oracle_moves="R U R' U R U R' F' R U R' U' R' F R2 U' R' U2 R U' R'",
        orientation=ORI,
        description=(
            "The entire cube is solved except for the top layer permutation. The top face is "
            "entirely yellow (OLL is done). Two corners need to swap: the yellow-red-blue corner "
            "is at UBR (should be at UFL) and the yellow-green-orange corner is at UFL (should be "
            "at UBR). Two edges also need to swap: the yellow-blue edge is at UR (should be at UL) "
            "and the yellow-green edge is at UL (should be at UR). The UF edge, UB edge, UFR "
            "corner, and UBL corner are all in their correct positions. Execute a series of moves "
            "to solve the cube."
        ),
        difficulty="medium",
        cfop_stage="PLL",
        notes="PLL diagonal corner swap + adjacent edge swap. Standard orientation.",
    ))

    tasks.append(make_task(
        task_id="task_16_pll_adjacent_swap",
        oracle_moves="F R U' R' U' R U R' F' R U R' U' R' F R F'",
        orientation=ORI,
        description=(
            "The entire cube is solved except for the top layer permutation. The top face is "
            "entirely yellow (OLL is done). Two corners need to swap: the yellow-orange-blue "
            "corner is at UFR (should be at UBL) and the yellow-red-green corner is at UBL "
            "(should be at UFR). Two edges also need to swap: the yellow-blue edge is at UB "
            "(should be at UL) and the yellow-orange edge is at UL (should be at UB). The UF "
            "edge, UR edge, UFL corner, and UBR corner are all in their correct positions. "
            "Execute a series of moves to solve the cube."
        ),
        difficulty="medium",
        cfop_stage="PLL",
        notes="PLL adjacent corner swap + edge swap. Standard orientation.",
    ))

    # --- Task 17: Full scramble (hard) ---

    tasks.append(make_task(
        task_id="task_17_full_scramble",
        oracle_moves="F R2 D' F2 L2 U' F2 L2 U F2 L2 D2 L D B2 R2 F R' F L",
        orientation=('W', 'G', 'R'),
        description=(
            "You are holding the cube with white on top, green in front, and red on the right. "
            "The cube is fully scrambled.\n\n"
            "The top face (white center): back row (left to right) is yellow, green, orange; "
            "middle row is yellow, white, blue; front row is yellow, orange, white.\n\n"
            "The front face (green center): top row is orange, white, red; middle row is blue, "
            "green, yellow; bottom row is green, white, orange.\n\n"
            "The right face (red center): top row is blue, orange, blue; middle row is all red; "
            "bottom row is blue, red, orange.\n\n"
            "The bottom face (yellow center), looking up from below: front row (nearest the "
            "green face) is red, yellow, green; middle row is green, yellow, blue; back row "
            "(nearest the blue face) is red, green, white.\n\n"
            "The left face (orange center): top row is red, blue, green; middle row is orange, "
            "orange, white; bottom row is white, yellow, yellow.\n\n"
            "The back face (blue center), looking from behind: top row is yellow, red, blue; "
            "middle row is white, blue, green; bottom row is white, orange, green.\n\n"
            "Solve the cube."
        ),
        difficulty="hard",
        cfop_stage="full",
        notes="20-move random scramble from solved. Orientation (W, G, R). Tests full solving ability.",
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
