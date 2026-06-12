# Memory API and CLI Implementation Plan

Date: 2026-06-12
Status: Implemented in this feature branch

## Plan

1. Add `android_brain_memory.engine.MnemeMemory` as a thin facade over:
   - migration initialization,
   - salience scoring,
   - raw trace storage,
   - candidate-to-episode encoding,
   - episode storage,
   - fact upsert,
   - retrieval,
   - one-shot consolidation,
   - database inspection.
2. Add `android_brain_memory.cli` using `argparse` and JSON input/output.
3. Add `scripts/mneme_memory.py` as a repository-local wrapper.
4. Add integration tests for both the facade and CLI conversation-like flow.
5. Update README, runbook, backlog, and project memory.

## Files Changed

- `src/android_brain_memory/engine.py`
- `src/android_brain_memory/cli.py`
- `src/android_brain_memory/__init__.py`
- `scripts/mneme_memory.py`
- `tests/test_memory_engine_cli.py`
- `README.md`
- `docs/runbooks/MEMORY_CLI.md`
- `tasks/backlog.md`
- `memory/features/2026-06-12-memory-api-cli/`
- `memory/MEMORY_INDEX.md`

## Validation

- `python -m pytest tests/test_memory_engine_cli.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- CLI smoke commands against a temporary database

## Rollback

Remove the new facade, CLI wrapper, tests, and docs. Existing low-level memory modules are not rewritten by this feature.

## Definition of Done

- The facade and CLI can run candidate scoring, episode/fact storage, retrieval, consolidation, and inspection.
- JSON output is stable enough for Codex/replay/debug use.
- Existing lower-level tests still pass.
- Documentation and project memory are updated.
