# Email Draft — AfterQuery Take-Home Submission

**To:** samj@afterquery.com, research-hiring@afterquery.com
**Subject:** Take-Home Submission — Rubik's Cube Spatial Reasoning Benchmark (Robert Romani)

---

Hi Sam and team,

Attached is my take-home submission as a ZIP. The repo is in Harbor format and includes the full task suite, verifier, model results, and an oracle trajectory. A detailed writeup is included as `WRITEUP.md`.

Below are the requested explanations.

## 1. Task Design Rationale

The task tests multi-step spatial state tracking from natural language. A Rubik's Cube state is described in plain English — the way a human cuber would communicate it — and the model must output a move sequence that achieves a specified goal state.

This targets a capability class that matters for embodied AI: parsing natural language spatial descriptions, building an internal 3D representation, reasoning about how actions transform state, and outputting correct action sequences. The cube is an ideal testbed because there is zero room for approximation, as a single mis-tracked sticker cascades through all subsequent reasoning.

The benchmark includes 24 tasks across 4 difficulty tiers (easy/medium/hard/impossible), with anti-memorization measures (programmatic NL generation, varied orientations, random scrambles). It differs from CubeBench (Duan et al., 2025) in using natural language only (no symbolic state arrays or visual diagrams) and tests whether models can ground language in spatial structure rather than manipulate structured data.

A pass means the model correctly reconstructed 3D state from prose and planned a valid action sequence. A fail means it could not.

## 2. QC Methodology

The verifier is deterministic: it parses the model's declared orientation and moves, remaps moves to the absolute frame, applies them to the initial state array, and checks exact equality against the goal state. No partial credit, fuzzy matching, or human judgment.

Every task is round-trip verified at generation time — the oracle solution is applied to the scrambled state and confirmed to produce the goal. All 24 tasks pass this check.

The output parser is hardened against common model misbehaviors: it finds the last orientation tuple in the output (handling Claude's reasoning leakage), handles format variations, and correctly identifies INVALID declarations.

Fairness measures: complete move definitions in the prompt (both intuitive and explicit sticker-movement descriptions), identical prompt and API parameters for all models, orientation-invariant evaluation (models can choose any viewing frame), and temperature 0.6 for pass@2 consistency.

## 3. Training Signal Value

This task would improve several capabilities if used in training:

- **Spatial grounding from NL**: Converting prose descriptions of 3D configurations into accurate internal representations — transferable to navigation, assembly, and scene understanding tasks.
- **Multi-step state tracking**: Maintaining and updating state across sequential actions — transferable to any planning or execution task.
- **Reference frame reasoning**: Reasoning about the same physical reality from different perspectives — critical for robotics and multi-agent collaboration.
- **Impossibility detection**: Knowing when a task cannot be solved — directly relevant to AI safety and resource efficiency.

## 4. Time Estimate

~12 hours end to end:
- Day 1 (~6h): Cube simulator, 3D visualizer, evaluation harness, initial 11 tasks, first eval runs
- Day 2 (~6h): 13 additional tasks, parser hardening, instruction prompt hardening, full eval run, visualization tools; Clean eval, writeup, packaging, submission

## 5. Key Results (Summary)

| Model | Easy (7) | Medium (9) | Hard (4) | Impossible (4) | Total (24) |
|-------|----------|------------|----------|----------------|------------|
| Claude Opus 4.6 | 3.0 | 0.0 | 0.0 | 0.5 | **3.5 (14.6%)** |
| GPT 5.4 | 3.0 | 0.0 | 0.0 | 2.5 | **5.5 (22.9%)** |
| Gemini 3.1 Pro | 5.0 | 1.5 | 1.0 | 3.0 | **10.5 (43.8%)** |

The task is meaningfully hard for all three frontier models. The most interesting finding is complementary spatial blindness: Claude/GPT pass U/D but fail F/B/R/L single-move tasks, while Gemini shows the exact opposite pattern — suggesting different architectures handle horizontal vs. vertical plane rotations asymmetrically.

Full per-task breakdown, failure mode analysis, and timing data are in the attached `WRITEUP.md`.

Best,
Robert Romani
