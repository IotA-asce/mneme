# Local Runtime Events Implementation Plan

Date: 2026-06-12
Status: Implemented in this feature branch

## Plan

1. Add `src/android_brain_memory/runtime.py`.
2. Define event kind enums and a JSON-friendly `RuntimeEvent` dataclass.
3. Provide helper constructors for the seven required event categories.
4. Add a synchronous in-process `EventBus` with:
   - deterministic sequence numbers,
   - subscription handles,
   - optional event kind/source filters,
   - history inspection,
   - explicit TTL expiry.
5. Export runtime types from the package.
6. Add tests for publication, subscription, filtering, ordering, and expiry.
7. Document runtime boundaries in `docs/architecture/RUNTIME.md`.
8. Add durable project memory and index entry.

## Validation

- `python -m pytest tests/test_runtime_events.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

## Rollback

Remove `runtime.py`, runtime tests, exports, runtime documentation, implementation plan, and project memory entry. No migrations or persistent state are changed.

## Definition of Done

- The event layer is local, synchronous, deterministic, and documented.
- Tests prove subscription/filtering/order/expiry behavior.
- No ROS, asyncio, or new dependencies are added.
