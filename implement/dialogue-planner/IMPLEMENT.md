# Implementation Plan

## Phase 1 — Plan Model + Planner

- `dialogue.py`: `DialogueActType` (`answer`, `clarify`, `acknowledge`, `greet`), `UtterancePlan` dataclass (plan_id, act_type, created_ts, text, content_slots, memory_refs, confidence, intent_id, `to_dict()`), and `DialoguePlanner(store=None, source, clock)`:
  - `plan(intent, bundle=None, working=None) -> UtterancePlan | None`,
  - safety modes (frozen/degraded) and non-speaking intents (listen/look/idle/freeze/degraded) → `None`,
  - RESPOND_TO_USER: `clarify` when the intent's memory context flags `needs_clarification` (slot from the conflict warning), else `answer` from the top speakable fact (subject/predicate/value slots + memory ref), else `acknowledge` (memory instruction acknowledged explicitly), `greet` for greeting turns without memory,
  - REMEMBER_EVENT → `acknowledge`,
  - speakability: facts with `restricted` meta-memory are excluded from spoken references when a store is available; `never_say`/`internal_only` never appear (upstream retrieval guarantees, planner double-checks via store when present).

## Phase 2 — Tests (written first)

- `tests/test_dialogue.py`: answer with slots/refs/text, clarify on conflicts, acknowledge for memory instructions, greet for plain greetings, None for safety/listen/idle, restricted-fact exclusion, executive integration via `last_memory_bundle`, deterministic output.

## Phase 3 — Docs

- `docs/executive/DIALOGUE_PLANNER.md` (new); `MASTER_ROADMAP.md` M2.5; `REPO_STATUS.md`; memory entry + index.

## Validation

`python -m pytest tests/test_dialogue.py` → full suite → dev_check.

## Rollback

Revert new module/tests/docs; purely additive.

## Definition of Done

Utterance plans never reference unspeakable memory; act selection deterministic and covered by tests; full suite passes.
