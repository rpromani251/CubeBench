# Rubik's Cube Spatial Reasoning Benchmark

## 1. Task Design Rationale

### Motivation

Working with geospatial data this past semester emphasized the importance of being able to understand, interpret, and effectively manipulate spatial data — a known weakness of current LLMs. I wished to test this shortcoming via a game which tests competence in spatial relations and dealing with constraints: the Rubik's Cube.

### Capability Targeted

This benchmark tests **multi-step spatial state tracking from natural language** — the ability to:

1. Parse a natural-language description of a 3D object's state into an internal spatial representation
2. Reason about how actions transform that state
3. Output a correct action sequence achieving a specified goal

The task presents a Rubik's Cube state described in plain English (face colors, piece positions, orientations) and asks the model to produce a move sequence that solves it. Descriptions are written at the level a competent human cuber would use — specifying which stickers are misplaced and what the goal configuration is — without providing symbolic state arrays or visual diagrams.

### Why a Rubik's Cube?

The Rubik's Cube is an ideal testbed because it demands **exact spatial reasoning with no room for approximation**. Every move permutes 20 pieces across 6 faces simultaneously, and a single error in mental state tracking cascades through subsequent reasoning. Unlike tasks where partial credit or approximate answers are meaningful, the cube's discrete combinatorial structure means the model either tracks state correctly or it doesn't.

### Real-World Relevance

The cube is a synthetic proxy for a broadly important capability class:

- **Robotics instruction following** — parsing manipulation instructions and executing multi-step procedures in the correct order and orientation
- **Assembly and repair from manuals** — understanding part orientations and spatial relationships described in text
- **Navigation from text descriptions** — maintaining a mental model of a physical environment and planning actions
- **Any agent that must maintain and update a mental model of physical state** from natural language observations

These are precisely the capabilities needed as LLM-based agents move from text-only tasks into embodied and spatially grounded settings.

### Differentiation from CubeBench

The closest related work is **CubeBench** (Duan et al., 2025), which evaluates LLMs on Rubik's Cube tasks using symbolic state representations (explicit corner/edge position-orientation tuples) and visual diagrams. This test suite differs in a key way: input is given purely through natural language. Descriptions are written as a human cuber would communicate a cube state — "the top face has a yellow cross with three misoriented corners" — rather than as structured data.

This tests a fundamentally different capability. CubeBench measures whether a model can manipulate symbolic permutation data; this benchmark measures whether a model can **ground natural language in spatial structure** and reason over it. The NL descriptions contain all information a human expert needs to solve the task, but the model must first build its own internal representation before it can plan.

### Why This Is Hard for Models

Frontier models fail on this benchmark for several compounding reasons:

1. **No spatial grounding**: LLMs process text sequentially but cube state is inherently 3D. The model must construct and maintain a mental 54-sticker array from prose descriptions.
2. **State tracking across moves**: Each move simultaneously affects 20+ sticker positions. The model must correctly simulate these permutations without a physical or symbolic substrate.
3. **Orientation sensitivity**: The same physical move (e.g., "turn the right face clockwise") affects different absolute stickers depending on how the cube is held. Models must correctly resolve the reference frame.
4. **Cascading errors**: A single mis-tracked sticker position leads to an incorrect state, which makes all subsequent reasoning wrong. There is no graceful degradation.
5. **Anti-memorization design**: Tasks use programmatically generated states at varied orientations, preventing models from pattern-matching to known CFOP algorithms in their training data.

## 2. Task Suite Design

The benchmark comprises **24 tasks** across 4 difficulty tiers:

| Difficulty | Count | Description |
|-----------|-------|-------------|
| Easy | 7 | One-move tasks (U, D, F, B, R, L) + already-solved recognition |
| Medium | 9 | F2L pair insert, OLL cases (4 orientations), PLL cases, last-layer combos |
| Hard | 4 | Double F2L insert, full last layer (OLL+PLL), T-perm, 20-move full scramble |
| Impossible | 4 | Twisted corner, fake OLL, single edge swap, invalid orientation |

### Difficulty Calibration

- **Easy tasks** test basic spatial comprehension: can the model identify which single move undoes a one-move scramble? These establish a baseline.
- **Medium tasks** test multi-step algorithmic reasoning within a constrained subproblem (e.g., orient last-layer corners). Orientations are varied across tasks — (Y,B,R), (Y,R,G), (Y,G,O), (Y,O,B) — to prevent memorization of algorithms tied to a single reference frame.
- **Hard tasks** require chaining multiple subprocedures or solving from a fully scrambled state, demanding sustained state tracking over 10-20+ moves.
- **Impossible tasks** test a complementary capability: recognizing when a described configuration violates physical constraints (e.g., a single twisted corner, which is impossible on a real cube). The model should output `INVALID` rather than attempting a solution.

### Orientation-Invariant Evaluation

A key design feature: the model declares its viewing orientation as a `(Top, Front, Right)` color tuple, and all moves it outputs are interpreted relative to that frame. The verifier remaps moves to the absolute frame before applying them. This means:

- Models can choose whichever orientation feels natural
- The same physical solution can be expressed from any of 24 possible orientations
- There is no penalty for unconventional framing

### Anti-Memorization Measures

- Tasks use **programmatically generated NL descriptions** from computed state arrays, not hand-written descriptions of named cases
- Multiple orientations are used across tasks, so even if a model recognizes an OLL pattern, the algorithm must be adapted to the declared reference frame
- The full scramble task uses a random 20-move sequence, not a standard scramble from any database
- Impossible tasks have no "correct algorithm" to memorize — the model must reason about physical constraints

## 3. QC Methodology

### Verifier Design

The verifier is **deterministic and zero-ambiguity**:

1. Parse the model's declared orientation `(Top, Front, Right)`
2. Parse the move sequence from the model's output
3. Remap each move from the model's reference frame to the absolute frame using whole-cube rotation logic
4. Apply the remapped moves to the initial state array (54-element color vector)
5. Compare the resulting state to the goal state element-by-element

Pass if and only if the resulting state exactly equals the goal state. There is no partial credit, fuzzy matching, or human judgment involved.

### Round-Trip Verification

Every task is verified at generation time:

1. Start from a solved cube
2. Apply the inverse of the oracle solution to produce the initial state
3. Apply the oracle solution to the initial state
4. Confirm the result equals the goal state

All 24 tasks pass this round-trip check. This guarantees that (a) every solvable task has at least one valid solution and (b) every impossible task is genuinely impossible (verified by construction — the state cannot be reached from a solved cube by legal moves).

### Algorithmic Generation & Manual Verification

Task states are generated algorithmically from the simulator — not hand-written — eliminating transcription errors in cube configurations. All tasks were also manually verified against a physical cube, drawing on competitive cubing experience to catch any simulator bugs in move application or state representation.

### Parser Robustness

The output parser is designed to handle common model misbehaviors:

- **Reasoning leakage**: Some models (particularly Claude) output chain-of-thought before the answer despite explicit instructions not to. The parser finds the **last** orientation tuple in the output, skipping any earlier mentions in reasoning text.
- **Format variations**: Handles code fences, extra whitespace, and minor formatting differences.
- **INVALID detection**: Correctly identifies when the model declares a configuration impossible.

### Fair and Useful, Not Just Hard

A key design goal was ensuring the task is **fair and useful** rather than merely difficult. Several deliberate choices reflect this:

- The instruction prompt provides **complete move definitions** with both intuitive descriptions ("clockwise when looking at the face") and explicit sticker-movement descriptions, so models are not disadvantaged by ambiguous notation
- The same prompt is used for all models — no model-specific tuning
- Temperature is set to 0.0 for single runs (deterministic) and 0.6 for pass@k evaluation (controlled variation)
- All models are called through the same OpenRouter API with identical parameters
- **Orientation-invariant evaluation** means models are not penalized for choosing a non-standard reference frame — only the correctness of the solution matters
- **Easy tasks establish a diagnostic floor**: if a model fails a one-move task, the failure is clearly in spatial comprehension, not in the complexity of the procedure. This makes failures interpretable rather than just counting wrong answers.
- **Impossible tasks test a complementary capability** — recognizing unsolvable configurations is useful signal, not a trick. A model that always attempts a solution regardless of feasibility has a meaningful gap.

### Design Tradeoffs

- **NL-only vs. symbolic input**: Symbolic state arrays (as in CubeBench) would make the task easier to specify unambiguously but would test a different capability (permutation manipulation vs. spatial grounding). NL input is harder to get right — descriptions must be precise enough for a human expert — but tests the more practically relevant skill.
- **Orientation invariance vs. fixed frame**: Allowing models to declare their own orientation adds engineering complexity to the verifier but eliminates a major source of unfairness. Without it, a model might produce a correct solution in a different reference frame and be marked wrong.
- **Anti-memorization vs. recognizable patterns**: Using randomized orientations and programmatic generation means models can't pattern-match to named CFOP cases from training data. The tradeoff is that tasks may not correspond to well-known cubing scenarios, but this is precisely the point — we want to test reasoning, not recall.
- **Pass@2 vs. pass@1**: A single run at temperature 0 conflates model capability with sampling luck. Pass@2 at temperature 0.6 gives a more stable signal while keeping evaluation cost reasonable (144 total API calls).

## 4. Model Results

### Pass@2 Scores

Each task was run twice per model (temperature 0.6). A task earns 0.5 points per successful run, for a maximum of 1.0 per task (24 tasks total). 144 API calls across 3 models.

| Model | Easy (7) | Medium (9) | Hard (4) | Impossible (4) | **Total (24)** |
|-------|----------|------------|----------|----------------|----------------|
| Claude Opus 4.6 | 3.0 | 0.0 | 0.0 | 0.5 | **3.5 (14.6%)** |
| GPT 5.4 | 3.0 | 0.0 | 0.0 | 2.5 | **5.5 (22.9%)** |
| Gemini 3.1 Pro | 5.0 | 1.5 | 1.0 | 3.0 | **10.5 (43.8%)** |

### Per-Task Breakdown

**Easy tier** — one-move tasks + already-solved recognition:

| Task | Claude | GPT | Gemini |
|------|--------|-----|--------|
| U (clockwise) | 1.0 | 1.0 | 0.0 |
| D (clockwise) | 1.0 | 1.0 | 0.0 |
| F (clockwise) | 0.0 | 0.0 | 1.0 |
| B (clockwise) | 0.0 | 0.0 | 1.0 |
| R (clockwise) | 0.0 | 0.0 | 1.0 |
| L (clockwise) | 0.0 | 0.0 | 1.0 |
| No move (already solved) | 1.0 | 1.0 | 1.0 |

A striking pattern: Claude and GPT pass U and D but fail F/B/R/L, while Gemini shows the exact complement — passing F/B/R/L but failing U and D. All models correctly recognize an already-solved cube.

**Medium tier** — F2L, OLL, PLL subtasks:

All 9 medium tasks scored 0.0 for Claude and GPT. Gemini scored 1.0 on `oll_all_corners` and 0.5 on `oll_antisune` (one of two runs), for 1.5 total. No model solved any F2L, PLL, or last-layer combo task at this tier.

**Hard tier** — multi-step procedures and full scrambles:

Only Gemini scored, earning 1.0 on the T-perm task by reproducing the standard algorithm: `R U R' U' R' F R2 U' R' F'`. All other hard tasks (double F2L, full last layer, 20-move scramble) scored 0.0 across all models.

**Impossible tier** — physically impossible configurations:

| Task | Claude | GPT | Gemini |
|------|--------|-----|--------|
| Twisted corner | 0.0 | 1.0 | 1.0 |
| Fake OLL | 0.0 | 0.0 | 1.0 |
| Single edge swap | 0.5 | 1.0 | 1.0 |
| Invalid orientation | 0.0 | 0.5 | 0.0 |

GPT and Gemini are substantially better at impossibility detection than Claude, which almost always attempts a solution rather than outputting `INVALID`.

### Timing

| Model | Avg (s) | Min (s) | Max (s) |
|-------|---------|---------|---------|
| Claude Opus 4.6 | 6.9 | 1.8 | 28.8 |
| GPT 5.4 | 1.9 | 0.6 | 3.6 |
| Gemini 3.1 Pro | 39.4 | 8.6 | 143.6 |

GPT is fastest by a wide margin. Gemini's extended inference time (even with a 16K reasoning token cap) reflects its deeper deliberation, which correlates with its higher accuracy.

### Failure Mode Analysis

The models exhibit distinct failure patterns:

1. **Direction confusion**: Claude and GPT invert move direction on F/B/R/L faces (e.g., outputting `F'` or `F2` when the correct answer is `F`), while Gemini inverts U and D (outputting `U'` instead of `U`). This suggests each model has a different internal spatial coordinate system that only partially aligns with standard cube notation.

2. **Reasoning leakage**: Claude frequently outputs chain-of-thought before its answer despite explicit no-reasoning instructions. On the T-perm task, Claude began with a 20+ move sequence, then wrote "Wait, let me reconsider..." — the parser correctly extracts the final answer, but the model's visible uncertainty undermines solution quality.

3. **Memorization vs. adaptation**: Gemini's T-perm success appears to be algorithm recall — it reproduced the standard `R U R' U' R' F R2 U' R' F'` verbatim. However, this recall doesn't generalize: Gemini fails when similar PLL patterns appear at non-standard orientations in the medium tier.

4. **False INVALID declarations**: GPT declared the solvable T-perm task as `INVALID`, suggesting it conflates task difficulty with impossibility. Claude shows the opposite failure: it almost never outputs `INVALID`, even for genuinely impossible configurations like a single twisted corner.

5. **Complementary face blindness**: The U/D vs. F/B/R/L split in easy tasks is the most surprising finding. It suggests that horizontal-plane rotations (U/D) and vertical-plane rotations (F/B/R/L) engage different spatial reasoning circuits, and different model architectures handle them asymmetrically.

## 5. Training Signal Value

This benchmark provides training signal for several capability dimensions:

### Spatial Grounding from Natural Language
The most direct signal: can the model convert prose descriptions of 3D spatial configurations into accurate internal representations? Improving here would transfer to any task requiring spatial understanding from text (navigation, assembly, scene understanding).

### Multi-Step State Tracking
Each task requires maintaining and updating a complex state representation across a sequence of actions. Training on this capability would improve performance on any planning or execution task where the agent must track how its actions change the world.

### Reference Frame Reasoning
The orientation-invariant design specifically tests whether models can reason about the same physical reality from different perspectives. This is critical for robotics (where the agent's viewpoint changes) and collaborative tasks (where different participants describe the same scene from different angles).

### Impossibility Detection
The impossible tasks test a meta-cognitive capability: knowing when a task **cannot** be solved. This is directly relevant to AI safety — an agent that attempts impossible tasks wastes resources and may cause harm by taking actions that cannot achieve the stated goal.

### Compositional Reasoning
Hard tasks require composing multiple sub-procedures (OLL then PLL, or two F2L insertions). Training on this would improve the model's ability to decompose complex problems and chain solutions correctly.

## 6. Time Estimate

- **Day 1** (~5 hours): Cube simulator, visualizer, evaluation harness, 11 initial tasks, first eval runs
- **Day 2** (~6 hours): 13 additional tasks, parser and prompt hardening, full eval run, writeup, and packaging

**Total: ~11 hours**
