# Email Draft v2 — AfterQuery Take-Home Submission

**To:** samj@afterquery.com, research-hiring@afterquery.com
**Subject:** Take-Home Submission — Rubik's Cube Spatial Reasoning Benchmark (Robert Romani)

---

Dear Sam and team,

Good evening! Attached is my submission as a ZIP in Harbor format. A detailed writeup is in `WRITEUP.md` (if you wish to hear a bit more about my thoughts regarding this project), and an animated comparison of the human oracle solve vs. all three model attempts are in `eval_anim/`. Brief explanations regarding the project are below.

**Task design rationale.** Working with geospatial data this past semester emphasized the importance of being able to understand, interpret, and effectively manipulate spatial data--a known weakness of current LLMs. As such, I wished to test this shortcoming via a game which tests competence in spatial relations and constraints: the Rubik's Cube. The task I designed tests a model's capability to create a scene from natural language and track spatial states: a Rubik's Cube state is described in plain English, and the model must output a correct move sequence to solve it. This is a proxy for other spatially related tasks, like robotics instruction following, assembly from manuals, or navigation from text descriptions. The benchmark includes 24 tasks across 4 difficulty tiers (easy/medium/hard/impossible) with anti-memorization measures including programmatic NL generation and varied orientations. It differs from CubeBench (Duan et al., 2025) by using NL-only input rather than symbolic state arrays, testing whether models can ground language in spatial structure.

**QC methodology.** The verifier is deterministic: it parses the model's declared orientation and moves, remaps to the absolute frame, applies them to the state array, and checks exact equality against the goal state. Every task is verified at generation time — the oracle solution is applied to the scrambled state and confirmed to produce the goal. Task states are generated algorithmically from the simulator (not hand-written), eliminating transcription errors in cube configurations. I also manually verified all the tasks against a physical cube, drawing on competitive cubing experience to catch any simulator bugs. The output parser is hardened against reasoning leakage (finds last orientation tuple) and format variations. Fairness is ensured through identical prompts, API parameters, and orientation-invariant evaluation across all models.

**Training signal value.** This task would improve spatial grounding from natural language — converting natural language descriptions of 3D configurations into accurate internal representations, transferable to navigation and scene understanding. It also targets multi-step state tracking, reference frame reasoning (same physical reality from different perspectives), and impossibility detection. These capabilities are directly relevant as LLM-based agents move into embodied and spatially grounded settings.

**Time estimate.** Roughly 11 hours across 2 days. Day 1 (~5h): cube simulator, visualizer, evaluation harness, 11 initial tasks, first eval runs. Day 2 (~6h): 13 additional tasks, parser and prompt hardening, full eval run, writeup, and packaging.

**Results (pass@2, 24 tasks):**

| Model | Total |
|-------|-------|
| Claude Opus 4.6 | 3.5/24 (14.6%) |
| GPT 5.4 | 5.5/24 (22.9%) |
| Gemini 3.1 Pro | 10.5/24 (43.8%) |

Best,
Robert Romani
