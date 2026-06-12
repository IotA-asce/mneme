# Stage 3 Runtime and Virtual Head Implementation

## Phase 1: Runtime wiring

- Add `MnemeRuntime`.
- Construct and wire bus, memory engine, sensory echo, working memory, world model, context windows, attention, executive, dialogue planner, promoter, extractor, and consolidation daemon.
- Add deterministic `tick()` and clean shutdown.

## Phase 2: Peripheral discovery

- Add device/snapshot models.
- Add a backend interface.
- Ship a deterministic fake backend for tests and CI.
- Publish inventory as world-state updates.

## Phase 3: Terminal virtual head

- Add typed user-input ingestion as `speech_transcript` perception events.
- Emit explicit memory candidates for simple remember instructions.
- Generate dialogue plans from executive intents and render them as terminal text.

## Phase 4: Packaging and verification

- Add `mneme` console script.
- Preserve `mneme-memory` as the memory CLI console script.
- Add tests for startup discovery, device appearance/removal, typed memory/answer flow, scenario replay, context shutdown, and CLI JSON output.

## Validation steps

- `.venv/bin/python -m pytest tests/test_stage3_runtime.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/python scripts/dev_check.py`
- `git diff --check`

## Rollback notes

The feature is isolated to new runtime/peripheral/virtual-head modules, exports, console scripts, docs, tests, and project memory. Removing those additions returns the previous Stage 2 bench stack.

## Definition of done

- `mneme run` exists.
- Runtime loop wires the Stage 0-2 stack in one process.
- Fake device discovery publishes state deterministically.
- Scripted typed conversation can remember and answer from memory.
- Full developer check passes.
