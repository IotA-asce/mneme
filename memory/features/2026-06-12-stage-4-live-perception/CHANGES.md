# Changes

- Added `live_perception.py` with retention policy, frame/transcript models, live worker reports, backend contracts, scripted backends, and command adapters.
- Added `LiveVisionWorker` for camera keyframes, person detections from command JSON/sidecars, raw frame traces, and memory candidates.
- Added `LiveSpeechWorker` for transcripts, raw transcript traces, memory candidates, and deterministic remember-phrase semantic extraction.
- Added `PerceptionFusionCalibrator` for speaker/person match diagnostics.
- Integrated live workers into `MnemeRuntime` and `mneme run` command flags.
- Added frame archive retention defaults to `config/memory.yaml`.
- Added Stage 4 tests and runbook documentation.
