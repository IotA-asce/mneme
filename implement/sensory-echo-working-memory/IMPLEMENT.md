# Sensory Echo and Working Memory Implementation Plan

Date: 2026-06-12
Status: Implemented in this feature branch

## Plan

1. Add `src/android_brain_memory/working_memory.py`.
2. Define `EchoFragment`, `WorkingMemorySnapshot`, `SensoryEchoBuffer`, and `WorkingMemory`.
3. Integrate both components with `EventBus` through explicit `attach_to_bus()` methods.
4. Implement bounded retention:
   - echo fragments expire by TTL and max item count,
   - recent dialogue turns are capped,
   - recent event references are capped.
5. Add JSON snapshot export and optional persistence via `MemoryStore`.
6. Export public types from `android_brain_memory`.
7. Add tests for expiry, capacity limits, bus updates, snapshot export, and persistence.
8. Document behavior in `docs/memory/WORKING_MEMORY.md`.
9. Update backlog and project memory.

## Validation

- `python -m pytest tests/test_working_memory.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `git diff --check`

## Rollback

Remove the new working memory module, tests, docs, implementation plan, and project memory entry. No storage migrations are added.

## Definition of Done

- Echo and working memory are deterministic and bounded.
- Event bus integration is tested.
- Snapshot export and persistence are tested.
- Documentation explains boundaries and non-goals.
