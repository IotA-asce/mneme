# Implementation Plan

## Phase 1 — Lifecycle Event Kind

- Add `RuntimeEventKind.MEMORY_LIFECYCLE = "memory_lifecycle"` mapped to `RuntimeTopic.MEMORY`.
- Add `memory_lifecycle_event(source, lifecycle_stage, payload, ...)` factory mirroring the existing helpers.

## Phase 2 — Promoter

- `src/android_brain_memory/promotion.py`:
  - `PromotionOutcome` dataclass (candidate_id, decision, score, trace_id, episode_id, semantic_candidate, stored flags, lifecycle event id) with `to_dict()`.
  - `MemoryPromoter(engine, *, config=None, bus=None, source="memory_promoter", clock=None)`:
    - `attach_to_bus(bus)` / `detach_from_bus()` subscribing to `memory_candidate` events,
    - `handle_event(event)` extracting the candidate payload; malformed payloads increment `stats["skipped"]` and return `None`,
    - `promote(candidate)` scoring once, mapping decision → storage flags, delegating to `MnemeMemory.remember_candidate`, publishing a `memory_lifecycle` event with `lifecycle_stage="promotion"`,
    - `stats` counters (`handled`, `skipped`, per-decision counts).

## Phase 3 — Tests (written first)

- `tests/test_promotion.py`: decision→storage mapping for all four decisions, bus-driven promotion, malformed event skip, lifecycle event payload, and the stage exit criterion: full scenario replay with promoter attached produces durable trace + episode + provenance chain with no manual storage calls.

## Phase 4 — Docs and Status

- `docs/memory/PROMOTION.md` (new), `docs/architecture/RUNTIME.md` (ninth event kind), `docs/architecture/MASTER_ROADMAP.md` (M1.1 done), `docs/architecture/REPO_STATUS.md`.

## Validation

- `python -m pytest tests/test_promotion.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Event kind → promoter → tests green → docs.

## Rollback

Revert `promotion.py`, runtime additions, tests, docs. No schema changes.

## Definition of Done

- Replayed scenario yields documented storage outcomes deterministically with no manual calls.
- Promotion decisions observable as `memory_lifecycle` events.
- Full suite passes.
