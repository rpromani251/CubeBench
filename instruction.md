# Rubik's Cube: Solve from Natural Language State Description

You are an expert Rubik's Cube solver. You will be given a natural language description of a Rubik's Cube state using standard CFOP terminology. Your job is to output a sequence of moves in standard Rubik's Cube notation that achieves the described goal.

## Face Notation

The six faces of the cube are named relative to the viewer's perspective:
- **U** (Up): the top face
- **D** (Down): the bottom face
- **F** (Front): the face facing the viewer
- **B** (Back): the face away from the viewer
- **R** (Right): the face on the viewer's right
- **L** (Left): the face on the viewer's left

## Position Notation

Positions on the cube are described by the faces that meet at that location:

- **Edge positions** are named by the two faces that meet there. For example, **UF** is the edge where the Up face and Front face meet (top of the front face), **UR** is the edge where the Up and Right faces meet, and **FR** is the edge where the Front and Right faces meet.
- **Corner positions** are named by the three faces that meet there. For example, **UFR** is the corner where the Up, Front, and Right faces meet (top-right of the front face), and **UBL** is the corner where the Up, Back, and Left faces meet.

## CFOP Terminology

- **White cross**: the four white edge pieces are correctly placed on the Down face, forming a plus-sign pattern, with each edge's side color matching its adjacent center.
- **F2L (First Two Layers)**: after the cross, the bottom two layers are completed by inserting corner-edge pairs into the four slots between the D-layer cross edges. Each slot is named by the two side faces it sits between (e.g., the front-right slot is between the F and R faces).
- **OLL (Orientation of the Last Layer)**: all stickers on the U face are made the same color (typically yellow), without regard to the side colors of the U-layer pieces.
- **PLL (Permutation of the Last Layer)**: the U-layer pieces, already oriented from OLL, are permuted into their correct positions to solve the cube.

## Move Notation
- Face moves: `R`, `L`, `U`, `D`, `F`, `B` (clockwise 90° when looking directly at that face)
- Inverse moves: `R'`, `L'`, `U'`, `D'`, `F'`, `B'` (counter-clockwise 90°)
- Double moves: `R2`, `L2`, `U2`, `D2`, `F2`, `B2` (180°)
- Wide moves: `r`, `l`, `u`, `d`, `f`, `b` (and their inverses/doubles)
- Rotations: `x`, `y`, `z` (and their inverses/doubles)

## Output Format
Your response must be exactly two lines:

**Line 1:** Your orientation as a tuple `(Top, Front, Right)` using color letters: W=White, Y=Yellow, R=Red, O=Orange, G=Green, B=Blue. This declares how you are holding the cube — all moves you give will be interpreted relative to this orientation.

**Line 2:** A space-separated sequence of moves. No explanation, no commentary.

Example output:
```
(Y, R, G)
R U R' U R U2 R'
```

This means: "I am holding the cube with Yellow on top, Red in front, and Green on the right. From that perspective, perform R U R' U R U2 R'."

## Task
{{TASK_DESCRIPTION}}
