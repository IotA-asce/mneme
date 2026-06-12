# Stage 4 Live Perception Implementation

## Plan

1. Add live-perception dataclasses and backend contracts.
2. Add deterministic scripted camera/speech backends for tests.
3. Add command adapters for local frame capture and speech transcription tools.
4. Add `LiveVisionWorker`, `LiveSpeechWorker`, and `PerceptionFusionCalibrator`.
5. Integrate workers into `MnemeRuntime` as opt-in components.
6. Expose CLI flags for command adapters and retention limits.
7. Add tests for frame archive, transcript promotion, fusion, and command parsing.
8. Update runbooks, roadmap, backlog, and project memory.

## Files Changed

- `src/android_brain_memory/live_perception.py`
- `src/android_brain_memory/runtime_loop.py`
- `src/android_brain_memory/virtual_head.py`
- `src/android_brain_memory/__init__.py`
- `config/memory.yaml`
- `tests/test_live_perception.py`
- `docs/runbooks/LIVE_PERCEPTION.md`
- roadmap/status/backlog/memory files

## Validation

- Focused Stage 4 tests.
- Full pytest suite.
- Developer check.
- CLI smoke tests.

## Rollback

Disable live-perception worker construction and remove the CLI command-adapter flags. Fake discovery and typed runtime behavior remain intact.

## Definition of Done

- Live perception can publish camera frame, person seen, and speech transcript events through the same runtime bus.
- Raw frame/transcript traces preserve provenance and confidence.
- Important speech can become semantic memory through existing promotion/extraction.
- Frame archive retention is bounded and tested.
- Stage 4 docs explain command-adapter requirements and limitations.
