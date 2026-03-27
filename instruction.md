# Rubik's Cube: Solve from Natural Language State Description

**READ THIS ENTIRE DOCUMENT BEFORE RESPONDING. Do not begin reasoning until you have read every section, including the task at the bottom.**

## Output Format (CRITICAL — READ FIRST)

Your response MUST be **exactly two lines** and NOTHING ELSE. Do NOT include ANY reasoning, explanation, commentary, thinking, chain-of-thought, justification, or analysis. Do NOT preface your answer with phrases like "Here is my solution" or "Let me think about this." Do NOT append any explanation after the two lines. Your ENTIRE response is ONLY the two lines specified below — no text before, between, or after them.

**Line 1:** Your orientation as a tuple `(Top, Front, Right)` using color letters: W=White, Y=Yellow, R=Red, O=Orange, G=Green, B=Blue. This declares how you are holding the cube — all moves you give will be interpreted relative to this orientation. Use the standard orientation `(Y, R, G)` (Yellow top, Red front, Green right) unless you have a specific reason to choose otherwise.

**Line 2:** A space-separated sequence of moves. Nothing else. If the cube is already solved, output an empty second line. If the cube configuration is physically impossible (e.g., an invalid permutation that cannot exist on a real cube), output `INVALID` as the second line.

**Examples:**

Solving a scrambled cube:
```
(Y, R, G)
R U R' U R U2 R'
```

Cube is already solved (empty second line):
```
(Y, R, G)

```

Impossible configuration (second line is INVALID):
```
(Y, R, G)
INVALID
```

Any response that is not exactly two lines in this format will be marked as a failure. This includes responses that contain reasoning, explanations, or any text beyond the two required lines.

## Accuracy

Correctness is paramount. Your moves will be applied to the cube state programmatically and verified against the goal state. There is no partial credit. Make no mistakes — verify your solution mentally before outputting it.

## Allowed Moves

You may ONLY use moves from the list below. Any other notation (e.g., M, E, S, Rw, or slice moves) is not supported and will cause an automatic failure.

**"Clockwise" always means clockwise when you are looking directly at that face from outside the cube:**

- `R` (Right clockwise): Looking at the right face head-on, the top edge of R moves toward the front. Equivalently: the right column of F moves up, the right column of U moves to the back, the right column of B moves down, the right column of D moves to the front.
- `L` (Left clockwise): Looking at the left face head-on, the top edge of L moves toward the back. Equivalently: the left column of F moves down, the left column of D moves to the back, the left column of B moves up, the left column of U moves to the front.
- `U` (Up clockwise): Looking down at the top face, the front edge of U moves to the right. Equivalently: the top row of F moves to the right face, the top row of R moves to the back, the top row of B moves to the left, the top row of L moves to the front.
- `D` (Down clockwise): Looking up at the bottom face, the front edge of D moves to the left. Equivalently: the bottom row of F moves to the left face, the bottom row of L moves to the back, the bottom row of B moves to the right, the bottom row of R moves to the front.
- `F` (Front clockwise): Looking at the front face head-on, the top edge of F moves to the right. Equivalently: the bottom row of U moves to the right, the left column of R moves down, the top row of D moves to the left, the right column of L moves up.
- `B` (Back clockwise): Looking at the back face head-on (from behind the cube), the top edge of B moves to the right. Equivalently: the top row of U moves to the left, the right column of R moves up, the bottom row of D moves to the right, the left column of L moves down.

**Modifiers:**
- **Inverse** (`'`): `R'`, `L'`, `U'`, `D'`, `F'`, `B'` — counter-clockwise 90° (the reverse of the corresponding clockwise move)
- **Double** (`2`): `R2`, `L2`, `U2`, `D2`, `F2`, `B2` — 180° turn
- **Wide moves:** `r`, `l`, `u`, `d`, `f`, `b` — turn two layers instead of one (and their inverses/doubles)
- **Rotations:** `x`, `y`, `z` — whole-cube rotations following R, U, F respectively (and their inverses/doubles)

Do NOT use M, E, S, Mw, or any other notation not listed above.

## Reference: Face Notation

The six faces of the cube are named relative to the viewer's perspective:
- **U** (Up): the top face
- **D** (Down): the bottom face
- **F** (Front): the face facing the viewer
- **B** (Back): the face away from the viewer
- **R** (Right): the face on the viewer's right
- **L** (Left): the face on the viewer's left

## Reference: Position Notation

Positions on the cube are described by the faces that meet at that location:

- **Edge positions** are named by the two faces that meet there. For example, **UF** is the edge where the Up face and Front face meet (top of the front face), **UR** is the edge where the Up and Right faces meet, and **FR** is the edge where the Front and Right faces meet.
- **Corner positions** are named by the three faces that meet there. For example, **UFR** is the corner where the Up, Front, and Right faces meet (top-right of the front face), and **UBL** is the corner where the Up, Back, and Left faces meet.

## Reference: CFOP Terminology

- **White cross**: the four white edge pieces are correctly placed on the Down face, forming a plus-sign pattern, with each edge's side color matching its adjacent center.
- **F2L (First Two Layers)**: after the cross, the bottom two layers are completed by inserting corner-edge pairs into the four slots between the D-layer cross edges. Each slot is named by the two side faces it sits between (e.g., the front-right slot is between the F and R faces).
- **OLL (Orientation of the Last Layer)**: all stickers on the U face are made the same color (typically yellow), without regard to the side colors of the U-layer pieces.
- **PLL (Permutation of the Last Layer)**: the U-layer pieces, already oriented from OLL, are permuted into their correct positions to solve the cube.

## Task

{{TASK_DESCRIPTION}}
