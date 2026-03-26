"""
3D Rubik's Cube visualizer using matplotlib.

Renders from the user's perspective: Yellow top, Red front, Green right.
Absolute frame: U=Yellow(Z=3), F=Red(Y=0), R=Green(X=3), D=White(Z=0), L=Blue(X=0), B=Orange(Y=3).

Usage:
    python visualize.py                              # show solved state
    python visualize.py --task tasks/easy/task_01*.json  # show task initial state
    python visualize.py --task tasks/easy/task_01*.json --goal  # show goal state
    python visualize.py --task tasks/easy/task_01*.json --both  # side by side
    python visualize.py --state '["Y","Y","Y",...54 elements...]'
    python visualize.py --task tasks/easy/task_01*.json --moves "F R' F' R"
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from cube import Cube, SOLVED_STATE, U, R, F, D, L, B

# Color map: letter -> hex
COLOR_MAP = {
    'W': '#FFFFFF',
    'Y': '#FFD500',
    'R': '#B71234',
    'O': '#FF5800',
    'G': '#009B48',
    'B': '#0046AD',
}


def sticker_quad(origin, right, up):
    """Return 4 corners of a unit square given origin and two basis vectors."""
    o = np.array(origin, dtype=float)
    r = np.array(right, dtype=float)
    u = np.array(up, dtype=float)
    return [o, o + r, o + r + u, o + u]


def build_face_quads(face_offset, state):
    """Build 9 quads + colors for one face of the cube.

    3D coordinate system (matplotlib Z = up):
      X: Left(0) to Right(3)     abs L/Blue(X=0) .. abs R/Green(X=3)
      Y: Front(0) to Back(3)     abs F/Red at Y=0 (front), abs B/Orange at Y=3 (back)
      Z: Bottom(0) to Top(3)     abs D/White(Z=0) .. abs U/Yellow(Z=3)

    Now the absolute frame directly matches the user's view:
      F (Red)    at Y=0 = front, facing viewer
      R (Green)  at X=3 = right side
      U (Yellow) at Z=3 = top
      B (Orange) at Y=3 = back
      L (Blue)   at X=0 = left side
      D (White)  at Z=0 = bottom
    """
    quads = []
    colors = []

    gap = 0.03
    size = 1.0 - 2 * gap

    # Face sticker layout (looking at face from outside):
    #   0 1 2
    #   3 4 5
    #   6 7 8

    if face_offset == U:  # Z=3 plane (top), looking down
        # Looking down: front (F/Red, Y=0) at bottom, right (R/Green, X=3) at right
        # U face borders: row 0 -> B (Y=3), row 2 -> F (Y=0)
        #                 col 0 -> L (X=0), col 2 -> R (X=3)
        for i in range(9):
            row, col = divmod(i, 3)
            x = col + gap           # col 0=left(X=0), col 2=right(X=3)
            y = (2 - row) + gap     # row 0=back(Y=3), row 2=front(Y=0)
            quads.append(sticker_quad([x, y, 3], [size, 0, 0], [0, size, 0]))
            colors.append(COLOR_MAP[state[U + i]])

    elif face_offset == D:  # Z=0 plane (bottom)
        for i in range(9):
            row, col = divmod(i, 3)
            x = col + gap
            y = row + gap
            quads.append(sticker_quad([x, y, 0], [size, 0, 0], [0, size, 0]))
            colors.append(COLOR_MAP[state[D + i]])

    elif face_offset == F:  # Y=0 plane (front = red, facing viewer)
        # Looking from -Y at Y=0: X goes left to right, Z goes up
        # F borders: col 0 -> L (X=0), col 2 -> R (X=3), row 0 -> U (Z=3), row 2 -> D (Z=0)
        for i in range(9):
            row, col = divmod(i, 3)
            x = col + gap
            z = (2 - row) + gap
            quads.append(sticker_quad([x, 0, z], [size, 0, 0], [0, 0, size]))
            colors.append(COLOR_MAP[state[F + i]])

    elif face_offset == B:  # Y=3 plane (back = orange)
        # Looking from +Y at Y=3: X is mirrored (viewer's left = +X)
        for i in range(9):
            row, col = divmod(i, 3)
            x = (2 - col) + gap
            z = (2 - row) + gap
            quads.append(sticker_quad([x, 3, z], [size, 0, 0], [0, 0, size]))
            colors.append(COLOR_MAP[state[B + i]])

    elif face_offset == R:  # X=3 plane (right = green)
        # Looking from +X at X=3: col 0 borders F (Y=0), col 2 borders B (Y=3)
        # Viewer's right = F (low Y), viewer's left = B (high Y)
        # col 0 → low Y, col 2 → high Y (not mirrored)
        for i in range(9):
            row, col = divmod(i, 3)
            y = col + gap
            z = (2 - row) + gap
            quads.append(sticker_quad([3, y, z], [0, size, 0], [0, 0, size]))
            colors.append(COLOR_MAP[state[R + i]])

    elif face_offset == L:  # X=0 plane (left = blue)
        # Looking from -X at X=0: col 0 borders B (high Y), col 2 borders F (low Y)
        # Viewer's left = B (high Y), viewer's right = F (low Y)
        # col 0 → high Y, col 2 → low Y (mirrored)
        for i in range(9):
            row, col = divmod(i, 3)
            y = (2 - col) + gap
            z = (2 - row) + gap
            quads.append(sticker_quad([0, y, z], [0, size, 0], [0, 0, size]))
            colors.append(COLOR_MAP[state[L + i]])

    return quads, colors


def render_cube(state, title="Rubik's Cube", ax=None):
    """Render a 54-element cube state as a 3D plot.
    Camera shows: Yellow top, Red front (facing viewer), Green right."""
    show = ax is None
    if ax is None:
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

    all_quads = []
    all_colors = []

    for face_offset in [U, D, F, B, R, L]:
        quads, colors = build_face_quads(face_offset, state)
        all_quads.extend(quads)
        all_colors.extend(colors)

    poly = Poly3DCollection(all_quads, facecolors=all_colors,
                            edgecolors='#1a1a1a', linewidths=1.5)
    ax.add_collection3d(poly)

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect([1, 1, 1])
    ax.set_title(title)

    # Camera: see top (Z+), front/Y=0 (looking from -Y), and right/X=3
    # elev=25 looks slightly down, azim=-55 positions camera at front-right
    ax.view_init(elev=25, azim=-55)

    # Hide axes for clean look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('w')
    ax.yaxis.pane.set_edgecolor('w')
    ax.zaxis.pane.set_edgecolor('w')
    ax.grid(False)

    if show:
        plt.tight_layout()
        plt.show()

    return ax


def render_side_by_side(state1, state2, title1="Initial", title2="Goal"):
    """Render two cube states side by side."""
    fig = plt.figure(figsize=(14, 7))
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')
    render_cube(state1, title=title1, ax=ax1)
    render_cube(state2, title=title2, ax=ax2)
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="3D Rubik's Cube visualizer")
    parser.add_argument("--task", type=str, help="Path to task JSON file")
    parser.add_argument("--goal", action="store_true", help="Show goal state instead of initial")
    parser.add_argument("--both", action="store_true", help="Show initial and goal side by side")
    parser.add_argument("--state", type=str, help="Raw 54-element state array as JSON string")
    parser.add_argument("--moves", type=str, help="Apply moves to the state before displaying")
    parser.add_argument("--orientation", type=str,
                        help="Orientation for moves, e.g. 'Y,R,G'")
    args = parser.parse_args()

    if args.state:
        state = json.loads(args.state)
        c = Cube(state)
        if args.moves:
            if args.orientation:
                top, front, right = args.orientation.split(',')
                c.apply_moves_oriented(args.moves, top.strip(), front.strip(), right.strip())
            else:
                c.apply_moves(args.moves)
        render_cube(c.state, title="Custom State")

    elif args.task:
        with open(args.task) as f:
            task = json.load(f)

        if args.both:
            if args.moves:
                c_after = Cube(task["initial_state"])
                if args.orientation:
                    top, front, right = args.orientation.split(',')
                    c_after.apply_moves_oriented(args.moves, top.strip(), front.strip(), right.strip())
                else:
                    ori = task.get("orientation")
                    if ori:
                        c_after.apply_moves_oriented(args.moves, *ori)
                    else:
                        c_after.apply_moves(args.moves)
                render_side_by_side(task["initial_state"], c_after.state,
                                    title1="Initial", title2="After Moves")
            else:
                render_side_by_side(task["initial_state"], task["goal_state"],
                                    title1=f"Initial ({task['id']})",
                                    title2=f"Goal ({task['id']})")
        elif args.goal:
            render_cube(task["goal_state"], title=f"Goal: {task['id']}")
        else:
            state = task["initial_state"]
            c = Cube(state)
            if args.moves:
                if args.orientation:
                    top, front, right = args.orientation.split(',')
                    c.apply_moves_oriented(args.moves, top.strip(), front.strip(), right.strip())
                else:
                    ori = task.get("orientation")
                    if ori:
                        c.apply_moves_oriented(args.moves, *ori)
                    else:
                        c.apply_moves(args.moves)
                render_cube(c.state, title=f"After Moves: {task['id']}")
            else:
                render_cube(state, title=f"Initial: {task['id']}")
    else:
        render_cube(SOLVED_STATE, title="Solved Cube")


if __name__ == "__main__":
    main()
