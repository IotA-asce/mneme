# Changes

- Added optional dependency extras in `pyproject.toml` for local audio, VAD, ASR, TTS, vision, local-speech, local-vision, and local-lab profiles.
- Added `local_audio.py` with bounded sounddevice capture, WebRTC VAD wrapper, faster-whisper ASR backend, and Kokoro TTS backend.
- Added `local_vision.py` with OpenCV frame capture and MediaPipe face/person observations.
- Added `local_models.py` and `config/models.yaml` for local model registry/list/verify/download support.
- Added `local_ui.py` for a stdlib-served browser dashboard.
- Added `evaluation.py` for local JSONL daily-driver metrics.
- Extended `mneme` CLI with local profiles, `ui`, `models`, and `eval` commands.
- Added Stage 6 tests with fake devices/models.
- Updated README, roadmap/status docs, prerequisites, backlog, runbooks, implementation records, and memory index.
