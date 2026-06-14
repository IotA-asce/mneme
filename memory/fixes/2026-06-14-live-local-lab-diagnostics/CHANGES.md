# Changes

- Added task-API support to `MediaPipeFaceDetectionBackend`.
- Added `--face-model-path` with the default `.local/models/mediapipe/face_detector.task`.
- Preserved OpenCV camera frames when face detection fails, recording `face_detector_error` metadata.
- Added live console status for vision capture failures and detector unavailability.
- Added `LocalModelRegistry.verify(profile=...)` and `mneme models verify --profile ...`.
- Updated README, runbooks, repository status, backlog, implementation artifacts, and memory index.

