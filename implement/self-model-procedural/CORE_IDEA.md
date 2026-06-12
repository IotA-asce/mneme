# Core Idea: Self Model v0 and Procedural Memory v0 (Stage 2 / M2.6)

## Problem Statement

Two of the seven memory layers have no implementation at all: the robot has no persistent identity facts about itself (name, capabilities, limitations), and skill/timing parameters have nowhere typed to live — so future skills would hardcode values with no provenance or history.

## Desired Outcome

- **Self model v0** (`SelfModel`): identity facts about the robot stored through the existing fact machinery under a reserved subject (`self`). Deliberate identity updates replace in place (fixed fact ID per predicate) — an intentional update is not a contradiction. Self-queries answerable from ordinary retrieval; a deterministic `describe()` summary.
- **Procedural memory v0** (`ProceduralMemory`): typed skill parameters (`procedure:<skill>:<parameter>` predicates) with **explicit versioning**: each update creates a new versioned fact that supersedes the previous one (supersession chain + provenance notes), so parameter history is auditable. `get_parameter` returns the latest value; `parameter_history` returns the full chain. Storage and provenance only — **no autonomous learning** (Stage 7, bounded).

## Affected Systems

- `src/android_brain_memory/self_model.py` (new), `__init__.py`
- `tests/test_self_model.py` (new)
- `docs/memory/SELF_MODEL.md` (new), roadmap/status docs

## Assumptions / Constraints

- Both ride on the existing fact store: provenance, meta-memory, speakability, and retrieval come for free; no schema changes.
- Identity facts default `system_generated` (or `user_confirmed` when the user names the robot); procedural facts are `system_generated` — neither participates in the conservative user/inferred conflict rules, so updates are explicit, not conflict-driven.
- No parameter range enforcement here — the actuator bridge owns hard ranges (Stage 5/7).

## Non-Goals

- Autonomous self-modification or procedural learning (explicitly bounded to Stage 7).
- Emotion or personality modeling.

## Risks

- Reserved-subject collisions if user facts use subject "self"; documented convention, enforced by the helpers using a fixed subject.
