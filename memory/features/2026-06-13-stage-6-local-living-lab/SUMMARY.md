# Stage 6 Local Living Lab

Date: 2026-06-13
Status: Complete — foundation implemented

Stage 6 is now the brain-first Local Living Lab instead of physical embodiment. Mneme can keep developing on the current computer with optional local microphone, speaker, camera, local models, memory, attention, dialogue, virtual presence, and evaluation logs while motors and ROS remain deferred.

Implemented foundation:

- optional local extras for speech, VAD, ASR, TTS, vision, and combined local-lab installs,
- native local speech/vision/TTS backend wrappers behind existing interfaces,
- local model registry and `mneme models` CLI,
- runtime profiles for `local-speech`, `local-vision`, and `local-lab`,
- stdlib local browser dashboard through `mneme ui`,
- JSONL evaluation logging and `mneme eval summarize`,
- documentation, backlog, implementation notes, and project memory updates.

Real-device/model quality remains a manual validation task.
