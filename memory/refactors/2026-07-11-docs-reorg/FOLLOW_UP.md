# Follow-up

## Package rename (deferred, code-level)

The Python package is still `src/android_brain_memory/`, reflecting the former
project name. A full rename to a Mneme-aligned package name would touch:

- `src/android_brain_memory/` directory and every import.
- `pyproject.toml` (`android-brain-memory` distribution name, console-script
  entry points, `.egg-info`).
- `.local/android_brain_memory.sqlite3` default DB path.
- All doc code snippets / import examples that currently, correctly, reference
  `android_brain_memory` (in `docs/memory/*`, `docs/runbooks/*`, `docs/architecture/RUNTIME.md`).

This was intentionally NOT done as part of the docs reorg because it is a
behavior-affecting code change requiring its own `implement/` plan, migration
note, and test pass. Until then, `android_brain_memory` references in docs are
accurate and must not be "corrected".

## Legacy prompts

`prompts/codex/` contains legacy agent-intake prompts that still reference
`CODEX_CONTEXT.md` and `docs/IMPLEMENTATION_PLAN.md` (both moved/renamed). Left
as-is (dated legacy artifacts). Revisit if the Codex intake flow is still used.
