# Stage 4 Real Device Discovery Core Idea

## Problem

Stage 3 runs Mneme as a terminal virtual head, but it only reports deterministic fake peripherals. Before live camera or microphone perception can be added, the runtime needs a safe way to inventory the host machine's cameras, microphones, and speakers.

## Desired Outcome

Add a real discovery backend behind the existing peripheral discovery contract. It should detect available devices without opening sensors, recording audio, playing sound, or changing runtime architecture.

## Affected Systems

- Peripheral discovery
- Virtual head CLI
- Runtime startup inventory
- Runbook and roadmap documentation
- Tests for platform-specific parsing

## Constraints

- Keep fake discovery as the deterministic default for tests and CI.
- Do not add OpenCV, audio libraries, ASR, TTS, or hardware dependencies.
- Use best-effort platform inventory commands only.
- Device discovery must fail closed to an empty inventory instead of crashing the runtime.

## Non-Goals

- No camera frame capture.
- No microphone recording.
- No speaker playback.
- No face detection, speech recognition, or sound localization.
- No permission-management UI.

## Risks

- OS command output varies by platform and version.
- Some systems may not have the expected inventory tools installed.
- Discovery confirms device presence only, not usability or permission access.
