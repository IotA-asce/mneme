# Changes

- `src/android_brain_memory/executive.py`: `ExecutiveGoal`; goal stack APIs; `_select_intent` goal wrapper over `_select_base_intent`; timing gate; `_memory_context` + `_retrieve_for_dialogue` with `_cue_tokens`; idle rotation; new params (`engine`, `min_response_delay_ms`).
- `src/android_brain_memory/__init__.py`: `ExecutiveGoal` export.
- `tests/test_executive_v1.py` (new): 7 tests.
- `docs/executive/EXECUTIVE_V0.md` v1 section; `MASTER_ROADMAP.md` M2.4 complete; `REPO_STATUS.md`.
- `implement/executive-v1/` planning files.
