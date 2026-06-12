# Stage 6 Local Living Lab — Implementation Plan

Date: 2026-06-13
Status: Implemented foundation

## Phases

1. Roadmap correction
   - Rename the next active stage to Stage 6 Local Living Lab.
   - Move physical embodiment to a deferred later stage.

2. Optional local backends
   - Add optional extras for local audio, VAD, ASR, TTS, vision, local-speech, local-vision, and local-lab.
   - Add native backend classes behind existing speech/vision/output contracts.
   - Preserve command adapters and simulated backends.

3. Local model management
   - Add `config/models.yaml`.
   - Add a registry API with list, verify, and guarded download.
   - Add CLI commands under `mneme models`.

4. Runtime/UI/evaluation
   - Add `mneme run --profile local-speech/local-vision/local-lab`.
   - Add `mneme ui` served by the standard library.
   - Add JSONL evaluation logging and `mneme eval summarize`.

5. Documentation and memory
   - Update README, roadmap, repo status, prerequisites, backlog.
   - Add Local Living Lab and model runbooks.
   - Record project memory and testing.

## Files Changed

- `pyproject.toml`
- `config/models.yaml`
- `src/android_brain_memory/local_audio.py`
- `src/android_brain_memory/local_vision.py`
- `src/android_brain_memory/local_models.py`
- `src/android_brain_memory/local_ui.py`
- `src/android_brain_memory/evaluation.py`
- `src/android_brain_memory/virtual_head.py`
- `tests/test_stage6_local_living_lab.py`
- README/docs/backlog/memory files

## Validation

- Focused Stage 6 tests.
- Existing live-perception and conversational-presence tests.
- Full local developer check.
- CLI smoke checks for model registry, model verification, runtime evaluation logging, and evaluation summary.

## Rollback

Remove the new Stage 6 modules and CLI branches, revert `pyproject.toml` extras and `config/models.yaml`, and restore roadmap/status docs to the previous Stage 5 state. No database migration was added, so rollback does not require schema changes.

## Definition of Done

- Base install remains lightweight.
- Optional backends are dependency-isolated.
- Existing command/simulated adapters still work.
- Fake-model/device tests cover new wrappers.
- Docs explain how to run and what remains manually validated.
- Project memory and backlog are updated.
