# Rules

- The planner produces structured plans only — no TTS, no skill goals, no actuator behavior, no bus publication in v0.
- Speakability is non-negotiable: `never_say`/`internal_only` content must never appear in a plan; `restricted` facts are excluded from spoken references when meta-memory is checkable.
- Safety silence: frozen/degraded modes yield no plan.
- The dialogue planner must not own the robot: it consumes intent, never generates it (AGENTS.md §10).
- Deterministic templates and act selection; no LLM in v0. Tests first (red).
