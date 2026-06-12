# Changes

- `src/android_brain_memory/engine.py`: opt-in `event_bus`/`event_source`/`clock` on `MnemeMemory`; retrieval and conflict lifecycle events.
- `src/android_brain_memory/storage.py`: `get_meta_memory_with_decay(limit)`.
- `src/android_brain_memory/cli.py`: `inspect-provenance`, `inspect-decay` commands.
- `tests/test_observability.py` (new): 6 tests.
- Docs: `docs/runbooks/MEMORY_CLI.md` new commands; `docs/memory/PROVENANCE.md` observability note; `MASTER_ROADMAP.md` M1.5 + Stage 1 complete; `REPO_STATUS.md`.
- `implement/memory-observability/` planning files.
