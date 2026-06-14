# Live Local Lab Diagnostics Implementation

## Changes

- Extend `MediaPipeFaceDetectionBackend` to support both legacy `solutions.face_detection` and task-based `FaceDetector` installations.
- Add `--face-model-path`, defaulting to `.local/models/mediapipe/face_detector.task`.
- Preserve OpenCV camera frames when optional face detection fails, adding `face_detector_error` metadata.
- Add live console lines for vision capture failures and face-detector unavailability.
- Add `mneme models verify --profile ...` for profile-scoped troubleshooting.
- Update README/runbooks/backlog/status/memory.

## Validation

```bash
.venv/bin/python -m pytest tests/test_stage6_local_living_lab.py tests/test_conversational_presence.py tests/test_live_perception.py -q
.venv/bin/mneme models verify --profile local-speech --json
.venv/bin/mneme models verify mediapipe_face_detector --json
git diff --check
.venv/bin/python scripts/dev_check.py
```

## Rollback Notes

The change is isolated to optional local vision/model CLI diagnostics. Rolling back restores the previous `mediapipe.solutions`-only wrapper and removes profile filtering from `models verify`.

