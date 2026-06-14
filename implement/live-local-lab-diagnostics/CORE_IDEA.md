# Live Local Lab Diagnostics Core Idea

## Problem

The local-lab live loop exposed two setup failures during manual testing:

- `--face-backend mediapipe` crashed when the installed MediaPipe package exposed the task API but not `mediapipe.solutions`.
- The live ASR failure hint suggested `mneme models verify --profile local-speech --json`, but that command was not supported yet.

Both failures blocked the local living-lab path from feeling inspectable. A missing optional model should be visible as runtime status, not a traceback.

## Desired Outcome

- Keep camera frames flowing when optional face detection is unavailable.
- Report missing or incompatible face detection as live status and frame metadata.
- Support profile-filtered model verification for local-speech troubleshooting.
- Preserve deterministic tests and avoid adding required dependencies.

## Non-Goals

- Do not bundle or auto-download MediaPipe model assets.
- Do not add identity recognition or emotion interpretation.
- Do not change the executive, dialogue, or actuator boundaries.

