# Context

A manual `mneme run --profile local-lab --live --json` run showed camera frames and ASR failures correctly in the live console. Follow-up commands exposed two remaining problems:

- `mneme run --profile local-vision --face-backend mediapipe --live` crashed with `AttributeError: module 'mediapipe' has no attribute 'solutions'`.
- `mneme models verify --profile local-speech --json` failed argument parsing, even though live speech diagnostics recommended that command.

The installed MediaPipe package exposed `mediapipe.tasks`, not the legacy `solutions` API. The repository already tracked a `mediapipe_face_detector` model record, but live vision did not expose a model path or degrade when the local model file was missing.

