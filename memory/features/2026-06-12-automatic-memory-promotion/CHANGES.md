# Changes

## Source

- `src/android_brain_memory/promotion.py` (new): `MemoryPromoter`, `PromotionOutcome`, decision→storage mapping constants.
- `src/android_brain_memory/runtime.py`: `RuntimeEventKind.MEMORY_LIFECYCLE` (topic `memory`), `memory_lifecycle_event()` helper.
- `src/android_brain_memory/__init__.py`: exports.

## Tests

- `tests/test_promotion.py` (new): lifecycle event kind/topic, all four decision mappings, bus-driven promotion with lifecycle payload assertions, malformed-event skip, scenario-replay end-to-end with provenance chain verification.

## Docs

- `docs/memory/PROMOTION.md` (new).
- `docs/architecture/RUNTIME.md`: ninth event kind, helper, boundary rule.
- `docs/architecture/MASTER_ROADMAP.md`: M1.1 marked complete.
- `docs/architecture/REPO_STATUS.md`: promotion implemented; stale not-implemented entry removed.

## Planning

- `implement/automatic-memory-promotion/` (CORE_IDEA, IMPLEMENT, RULES).

## Design Notes

- The promoter scores once to decide, and `remember_candidate` re-scores internally; scoring is deterministic so results are identical (documented as acceptable V1 cost).
- Working-memory candidates persist a raw trace (not nothing) so the turn's context remains traceable; echo-only candidates write nothing durable.
