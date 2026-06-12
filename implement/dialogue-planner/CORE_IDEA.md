# Core Idea: Dialogue Planner v0 (Stage 2 / M2.5)

## Problem Statement

Executive intents say *that* Mneme should respond, but nothing decides *what kind* of utterance to produce or which memories are safe to speak. There is no structured bridge between intent + memory bundle and a future speech skill.

## Desired Outcome

A deterministic, intent-level `DialoguePlanner`: given an executive intent (plus the memory bundle and optionally working context), produce a structured `UtterancePlan` — act type (`answer`, `clarify`, `acknowledge`, `greet`), content slots, template-realized text, and speakability-filtered memory references — or `None` when speaking is inappropriate (safety modes, listen/look/idle intents).

## User / Project Value

Completes the bench cognition chain: perception → world model → attention → memory → executive → *utterance plan*. The future speech skill (Stage 5) consumes plans; LLM realization (Stage 7) can later replace templates behind the same interface.

## Affected Systems

- `src/android_brain_memory/dialogue.py` (new), `__init__.py`
- `tests/test_dialogue.py` (new)
- `docs/executive/DIALOGUE_PLANNER.md` (new), roadmap/status docs

## Assumptions / Constraints

- No LLM, no external services: template-based realization, deterministic act selection.
- Speakability is enforced twice: retrieval already excludes `never_say`/`internal_only`; the planner additionally excludes `restricted` facts from spoken references when a store is available to check meta-memory, and never quotes memory the bundle did not provide.
- Safety modes produce no utterance plans — the planner is silent when the robot is frozen/degraded.

## Non-Goals

- Speech synthesis or timing (skills, Stage 5); LLM realization (Stage 7); multi-turn dialogue strategy.

## Risks

- Template text quality is placeholder-grade; acceptable, the contract is the structured plan.
