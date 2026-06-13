# Implementation Plan

## Steps

1. Add a runtime-level `refresh_devices()` method that performs an immediate device scan.
2. Add a UI **Refresh list** action and live select-option rendering from `/state`.
3. Extend deterministic dialogue planning to use:
   - source-aware fact phrasing,
   - episode fallback answers,
   - parsed memory acknowledgments,
   - current-turn fallback responses.
4. Update tests for UI rescan, device dropdown rendering, and dialogue grounding.
5. Update runbooks, status docs, backlog, and project memory.

## Validation

- Targeted tests:
  - `tests/test_dialogue.py`
  - `tests/test_stage6_local_living_lab.py`
  - `tests/test_real_peripherals.py`
- Compile check for `src/android_brain_memory`.
- Full developer check before commit.

## Rollback

Revert the UI route/JS changes and restore the previous dialogue templates if the behavior causes regressions.
