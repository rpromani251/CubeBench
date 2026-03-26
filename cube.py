"""
Rubik's Cube simulator using a 54-element array representation.

Faces are indexed as:
  U (Up)    = indices 0-8
  R (Right) = indices 9-17
  F (Front) = indices 18-26
  D (Down)  = indices 27-35
  L (Left)  = indices 36-44
  B (Back)  = indices 45-53

Each face is laid out as:
  0 1 2
  3 4 5
  6 7 8

Colors: W=White, R=Red, G=Green, Y=Yellow, O=Orange, B=Blue
Standard orientation: U=Yellow, F=Red, R=Green, D=White, L=Blue, B=Orange
"""

import copy

# Face offsets
U, R, F, D, L, B = 0, 9, 18, 27, 36, 45

# --- Orientation mapping ---

# Map each color to which absolute face it lives on in solved state
COLOR_TO_FACE = {
    'Y': U, 'G': R, 'R': F, 'W': D, 'B': L, 'O': B
}

OPPOSITE_COLOR = {
    'Y': 'W', 'W': 'Y', 'G': 'B', 'B': 'G', 'O': 'R', 'R': 'O'
}

FACE_OFFSET_TO_NAME = {U: 'U', R: 'R', F: 'F', D: 'D', L: 'L', B: 'B'}

# Which whole-cube rotation follows each absolute face
FACE_TO_ROTATION = {
    R: 'x',  L: "x'",
    U: 'y',  D: "y'",
    F: 'z',  B: "z'",
}


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


def get_orientation_map(top, front, right):
    """Given an orientation as (top_color, front_color, right_color),
    return a dict mapping relative face letters to absolute face offsets."""
    return {
        'U': COLOR_TO_FACE[top],
        'D': COLOR_TO_FACE[OPPOSITE_COLOR[top]],
        'F': COLOR_TO_FACE[front],
        'B': COLOR_TO_FACE[OPPOSITE_COLOR[front]],
        'R': COLOR_TO_FACE[right],
        'L': COLOR_TO_FACE[OPPOSITE_COLOR[right]],
    }


def remap_move(move_str, face_map):
    """Remap a single move from the LLM's orientation to absolute notation."""
    move_str = move_str.strip()
    if not move_str:
        return move_str

    # Parse modifier (' or 2)
    if len(move_str) >= 2 and move_str[-1] == "'":
        base, modifier = move_str[:-1], "'"
    elif len(move_str) >= 2 and move_str[-1] == '2':
        base, modifier = move_str[:-1], "2"
    else:
        base, modifier = move_str, ""

    # Face moves (R, L, U, D, F, B)
    if base in 'URFDLB':
        abs_name = FACE_OFFSET_TO_NAME[face_map[base]]
        return abs_name + modifier

    # Wide moves (r, l, u, d, f, b) — same remap, lowercase
    if base in 'urfdlb':
        abs_name = FACE_OFFSET_TO_NAME[face_map[base.upper()]].lower()
        return abs_name + modifier

    # Rotations (x, y, z)
    axis_to_relative_face = {'x': 'R', 'y': 'U', 'z': 'F'}
    if base in axis_to_relative_face:
        rel_face = axis_to_relative_face[base]
        abs_offset = face_map[rel_face]
        abs_rot = FACE_TO_ROTATION[abs_offset]  # e.g. 'x', "z'", etc.

        # Apply the move's modifier on top of the rotation's inherent direction
        if abs_rot.endswith("'"):
            abs_base = abs_rot[:-1]
            inverted = True
        else:
            abs_base = abs_rot
            inverted = False

        if modifier == "'":
            # Invert: flip the direction
            return abs_base if inverted else abs_base + "'"
        elif modifier == "2":
            # 180° — direction doesn't matter
            return abs_base + "2"
        else:
            return abs_rot

    return move_str  # Unknown — pass through


def remap_moves(moves_str, face_map):
    """Remap a full space-separated move sequence to absolute notation."""
    return ' '.join(remap_move(m, face_map) for m in moves_str.split())

SOLVED_STATE = [
    # U face (Yellow)
    'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y',
    # R face (Green)
    'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G',
    # F face (Red)
    'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R',
    # D face (White)
    'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W',
    # L face (Blue)
    'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B',
    # B face (Orange)
    'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O',
]


class Cube:
    def __init__(self, state=None):
        if state is None:
            self.state = list(SOLVED_STATE)
        else:
            self.state = list(state)

    def copy(self):
        return Cube(self.state)

    def _rotate_face_cw(self, face_offset):
        """Rotate the stickers on a face 90° clockwise."""
        s = self.state
        o = face_offset
        tmp = [s[o+0], s[o+1], s[o+2],
               s[o+3], s[o+4], s[o+5],
               s[o+6], s[o+7], s[o+8]]
        s[o+0], s[o+1], s[o+2] = tmp[6], tmp[3], tmp[0]
        s[o+3], s[o+4], s[o+5] = tmp[7], tmp[4], tmp[1]
        s[o+6], s[o+7], s[o+8] = tmp[8], tmp[5], tmp[2]

    def _rotate_face_ccw(self, face_offset):
        """Rotate the stickers on a face 90° counter-clockwise."""
        for _ in range(3):
            self._rotate_face_cw(face_offset)

    def _rotate_face_180(self, face_offset):
        """Rotate the stickers on a face 180°."""
        for _ in range(2):
            self._rotate_face_cw(face_offset)

    # === Basic moves ===

    def move_R(self):
        s = self.state
        self._rotate_face_cw(R)
        tmp = [s[U+2], s[U+5], s[U+8]]
        s[U+2], s[U+5], s[U+8] = s[F+2], s[F+5], s[F+8]
        s[F+2], s[F+5], s[F+8] = s[D+2], s[D+5], s[D+8]
        s[D+2], s[D+5], s[D+8] = s[B+6], s[B+3], s[B+0]
        s[B+0], s[B+3], s[B+6] = tmp[2], tmp[1], tmp[0]

    def move_L(self):
        s = self.state
        self._rotate_face_cw(L)
        tmp = [s[U+0], s[U+3], s[U+6]]
        s[U+0], s[U+3], s[U+6] = s[B+8], s[B+5], s[B+2]
        s[B+2], s[B+5], s[B+8] = s[D+6], s[D+3], s[D+0]
        s[D+0], s[D+3], s[D+6] = s[F+0], s[F+3], s[F+6]
        s[F+0], s[F+3], s[F+6] = tmp[0], tmp[1], tmp[2]

    def move_U(self):
        s = self.state
        self._rotate_face_cw(U)
        tmp = [s[F+0], s[F+1], s[F+2]]
        s[F+0], s[F+1], s[F+2] = s[R+0], s[R+1], s[R+2]
        s[R+0], s[R+1], s[R+2] = s[B+0], s[B+1], s[B+2]
        s[B+0], s[B+1], s[B+2] = s[L+0], s[L+1], s[L+2]
        s[L+0], s[L+1], s[L+2] = tmp[0], tmp[1], tmp[2]

    def move_D(self):
        s = self.state
        self._rotate_face_cw(D)
        tmp = [s[F+6], s[F+7], s[F+8]]
        s[F+6], s[F+7], s[F+8] = s[L+6], s[L+7], s[L+8]
        s[L+6], s[L+7], s[L+8] = s[B+6], s[B+7], s[B+8]
        s[B+6], s[B+7], s[B+8] = s[R+6], s[R+7], s[R+8]
        s[R+6], s[R+7], s[R+8] = tmp[0], tmp[1], tmp[2]

    def move_F(self):
        s = self.state
        self._rotate_face_cw(F)
        tmp = [s[U+6], s[U+7], s[U+8]]
        s[U+6], s[U+7], s[U+8] = s[L+8], s[L+5], s[L+2]
        s[L+2], s[L+5], s[L+8] = s[D+0], s[D+1], s[D+2]
        s[D+0], s[D+1], s[D+2] = s[R+6], s[R+3], s[R+0]
        s[R+0], s[R+3], s[R+6] = tmp[0], tmp[1], tmp[2]

    def move_B(self):
        s = self.state
        self._rotate_face_cw(B)
        tmp = [s[U+0], s[U+1], s[U+2]]
        s[U+0], s[U+1], s[U+2] = s[R+2], s[R+5], s[R+8]
        s[R+2], s[R+5], s[R+8] = s[D+8], s[D+7], s[D+6]
        s[D+6], s[D+7], s[D+8] = s[L+0], s[L+3], s[L+6]
        s[L+0], s[L+3], s[L+6] = tmp[2], tmp[1], tmp[0]

    # === Rotations ===

    def move_x(self):
        """Rotate entire cube on R axis (R direction)."""
        s = self.state
        self._rotate_face_cw(R)
        self._rotate_face_ccw(L)
        u_tmp = s[U+0:U+9]
        f_tmp = s[F+0:F+9]
        d_tmp = s[D+0:D+9]
        b_tmp = s[B+0:B+9]
        s[U+0:U+9] = f_tmp
        s[F+0:F+9] = d_tmp
        # B is "upside down" relative to the others
        s[D+0:D+9] = [b_tmp[8], b_tmp[7], b_tmp[6],
                       b_tmp[5], b_tmp[4], b_tmp[3],
                       b_tmp[2], b_tmp[1], b_tmp[0]]
        s[B+0:B+9] = [u_tmp[8], u_tmp[7], u_tmp[6],
                       u_tmp[5], u_tmp[4], u_tmp[3],
                       u_tmp[2], u_tmp[1], u_tmp[0]]

    def move_y(self):
        """Rotate entire cube on U axis (U direction)."""
        s = self.state
        self._rotate_face_cw(U)
        self._rotate_face_ccw(D)
        tmp = s[F+0:F+9]
        s[F+0:F+9] = s[R+0:R+9]
        s[R+0:R+9] = s[B+0:B+9]
        s[B+0:B+9] = s[L+0:L+9]
        s[L+0:L+9] = tmp

    def move_z(self):
        """Rotate entire cube on F axis (F direction)."""
        # z = rotation following F
        s = self.state
        self._rotate_face_cw(F)
        self._rotate_face_ccw(B)
        # Save all four side faces
        u_tmp = s[U+0:U+9]
        r_tmp = s[R+0:R+9]
        d_tmp = s[D+0:D+9]
        l_tmp = s[L+0:L+9]
        # U -> rotate CW becomes R
        s[R+0:R+9] = [u_tmp[6], u_tmp[3], u_tmp[0],
                       u_tmp[7], u_tmp[4], u_tmp[1],
                       u_tmp[8], u_tmp[5], u_tmp[2]]
        # R -> rotate CW becomes D
        s[D+0:D+9] = [r_tmp[6], r_tmp[3], r_tmp[0],
                       r_tmp[7], r_tmp[4], r_tmp[1],
                       r_tmp[8], r_tmp[5], r_tmp[2]]
        # D -> rotate CW becomes L
        s[L+0:L+9] = [d_tmp[6], d_tmp[3], d_tmp[0],
                       d_tmp[7], d_tmp[4], d_tmp[1],
                       d_tmp[8], d_tmp[5], d_tmp[2]]
        # L -> rotate CW becomes U
        s[U+0:U+9] = [l_tmp[6], l_tmp[3], l_tmp[0],
                       l_tmp[7], l_tmp[4], l_tmp[1],
                       l_tmp[8], l_tmp[5], l_tmp[2]]

    # === Derived moves ===

    def apply_move(self, move_str):
        """Apply a single move string like R, R', R2, etc."""
        move_str = move_str.strip()
        if not move_str:
            return

        base_moves = {
            'R': self.move_R, 'L': self.move_L, 'U': self.move_U,
            'D': self.move_D, 'F': self.move_F, 'B': self.move_B,
            'x': self.move_x, 'y': self.move_y, 'z': self.move_z,
        }

        # Wide moves: r = L x, etc.
        wide_moves = {
            'r': ['L', 'x'], 'l': ['R', 'x\''],
            'u': ['D', 'y'], 'd': ['U', 'y\''],
            'f': ['B', 'z'], 'b': ['F', 'z\''],
        }

        # Parse modifier
        if len(move_str) >= 2 and move_str[-1] == "'":
            base = move_str[:-1]
            modifier = "prime"
        elif len(move_str) >= 2 and move_str[-1] == '2':
            base = move_str[:-1]
            modifier = "double"
        else:
            base = move_str
            modifier = None

        # Handle wide moves
        if base in wide_moves:
            for sub_move in wide_moves[base]:
                if modifier == "prime":
                    self.apply_move(sub_move + "'")
                elif modifier == "double":
                    self.apply_move(sub_move + "2")
                else:
                    self.apply_move(sub_move)
            return

        if base not in base_moves:
            raise ValueError(f"Unknown move: {move_str}")

        fn = base_moves[base]
        if modifier == "prime":
            fn(); fn(); fn()  # 3x CW = CCW
        elif modifier == "double":
            fn(); fn()
        else:
            fn()

    def apply_moves(self, moves_str):
        """Apply a space-separated sequence of moves."""
        for move in moves_str.split():
            self.apply_move(move)

    def apply_moves_oriented(self, moves_str, top, front, right):
        """Apply moves interpreted from a given orientation (top, front, right colors).
        Remaps moves to absolute notation before applying."""
        face_map = get_orientation_map(top, front, right)
        self.apply_moves(remap_moves(moves_str, face_map))

    def get_face(self, face_offset):
        """Return 9-element list for a face."""
        return self.state[face_offset:face_offset+9]

    def __eq__(self, other):
        if isinstance(other, Cube):
            return self.state == other.state
        return False

    def __repr__(self):
        def face_str(offset):
            f = self.state[offset:offset+9]
            return f"  {f[0]} {f[1]} {f[2]}\n  {f[3]} {f[4]} {f[5]}\n  {f[6]} {f[7]} {f[8]}"

        return (
            f"U:\n{face_str(U)}\n"
            f"R:\n{face_str(R)}\n"
            f"F:\n{face_str(F)}\n"
            f"D:\n{face_str(D)}\n"
            f"L:\n{face_str(L)}\n"
            f"B:\n{face_str(B)}"
        )

    def is_solved(self):
        return self.state == SOLVED_STATE

    def face_solved(self, face_offset):
        """Check if a single face is uniform color."""
        f = self.state[face_offset:face_offset+9]
        return len(set(f)) == 1

    def cross_solved(self, face_offset=D):
        """Check if the cross is solved on a given face."""
        s = self.state
        center = s[face_offset + 4]
        edges = [face_offset + 1, face_offset + 3, face_offset + 5, face_offset + 7]
        return all(s[i] == center for i in edges)


def verify_solution(initial_state, goal_state, moves_str, orientation=None):
    """
    Verify that applying moves_str to initial_state produces goal_state.
    orientation: optional tuple (top, front, right) — if provided, moves are
    interpreted from that frame of reference.
    Returns (success: bool, resulting_state: Cube)
    """
    cube = Cube(initial_state)
    try:
        if orientation:
            top, front, right = orientation
            cube.apply_moves_oriented(moves_str, top, front, right)
        else:
            cube.apply_moves(moves_str)
    except ValueError as e:
        return False, str(e)
    return cube.state == goal_state, cube


if __name__ == "__main__":
    # Quick sanity check: R R' should return to solved
    c = Cube()
    c.apply_moves("R R'")
    assert c.is_solved(), "R R' should return to solved state"

    # Sexy move 6x should return to solved
    c = Cube()
    for _ in range(6):
        c.apply_moves("R U R' U'")
    assert c.is_solved(), "Sexy move x6 should return to solved state"

    # Orientation remapping: (Y, R, G) should be identity
    # U=Yellow, F=Red, R=Green matches the absolute frame
    fm = get_orientation_map('Y', 'R', 'G')
    assert remap_move('R', fm) == 'R'
    assert remap_move("U'", fm) == "U'"
    assert remap_move('F', fm) == 'F'
    assert remap_move('x', fm) == 'x'

    # Oriented moves with identity should match absolute
    c1 = Cube()
    c1.apply_moves("R U R' U'")

    c2 = Cube()
    c2.apply_moves_oriented("R U R' U'", 'Y', 'R', 'G')
    assert c1.state == c2.state, "Identity orientation should match absolute"

    print("All sanity checks passed.")
