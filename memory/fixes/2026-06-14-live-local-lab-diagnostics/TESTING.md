# Testing

Focused verification:

```bash
.venv/bin/python -m pytest tests/test_stage6_local_living_lab.py tests/test_conversational_presence.py tests/test_live_perception.py -q
.venv/bin/mneme models verify --profile local-speech --json
.venv/bin/mneme models verify mediapipe_face_detector --json
```

Result during implementation: 40 focused tests passed. Both model verification commands returned successfully and reported missing local files rather than parser/runtime errors.

Final verification:

```bash
git diff --check
.venv/bin/python scripts/dev_check.py
.venv/bin/mneme run --profile local-vision --face-backend mediapipe --live-ticks 1 --json
```

Result during implementation: `git diff --check` passed; `scripts/dev_check.py` completed DB init, smoke test, and 285 pytest tests. The bounded real local-vision smoke command exited successfully and reported `vision: camera returned no frame` because macOS/OpenCV was not authorized to capture video in this session.

Manual remaining validation:

- Place an approved MediaPipe face detector model at `.local/models/mediapipe/face_detector.task` or pass `--face-model-path`.
- Run `mneme run --profile local-vision --face-backend mediapipe --live` and confirm `person_seen` events are produced when a face is visible.
- Place or select a valid faster-whisper ASR model path before expecting live speech transcripts.
