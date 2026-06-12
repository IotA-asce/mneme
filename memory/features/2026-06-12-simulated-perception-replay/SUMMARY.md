# Simulated Perception Replay

Type: Feature
Date: 2026-06-12
Status: Complete

## Summary

Added deterministic simulated perception workers and scenario replay:

- face/person observation worker,
- speech transcript worker,
- sound direction worker,
- touch worker,
- body/internal health worker,
- YAML/JSON scenario loader,
- `ScenarioReplayRunner` that publishes events through the local runtime bus,
- optional memory candidate emission for important scenario steps,
- script wrapper for local replay,
- basic conversation fixture and replay tests.

No real camera, microphone, OpenCV, Whisper, audio library, ROS, hardware control, or new dependency was added.
