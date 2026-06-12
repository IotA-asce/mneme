# Stage 6 Local Living Lab — Core Idea

Date: 2026-06-13
Status: Implemented foundation

## Problem

The previous roadmap moved from virtual conversational presence toward physical embodiment too quickly. The project owner wants to develop and test Mneme's brain first on the current computer: camera, microphone, speaker, local models, memory, attention, virtual presence, and evaluation before motors or robot hardware.

## Desired Outcome

Stage 6 becomes **Local Living Lab**:

- local-first and cloud-optional,
- optional dependencies rather than heavy default install,
- native local speech and vision backends behind existing interfaces,
- local model hygiene before model sprawl,
- a lightweight browser UI that observes runtime state,
- evaluation logs for daily-driver brain-loop experiments,
- physical embodiment deferred.

## Affected Systems

- Runtime CLI (`mneme run`, `mneme ui`, `mneme models`, `mneme eval`)
- Live perception backend interfaces
- Speech output backend interface
- Model configuration
- README, roadmap, runbooks, backlog, project memory

## Assumptions

- Base install remains lightweight.
- Optional dependencies can be declared as extras.
- Tests use fake devices/models and do not require camera, microphone, speaker, OpenCV, faster-whisper, Kokoro, or MediaPipe.
- Real local validation happens manually on the current machine.

## Constraints

- No physical hardware control.
- No ROS runtime.
- No cloud dependency.
- No unrestricted face identity recognition.
- No emotion detection treated as truth.
- No model files committed to git.

## Non-Goals

- Polished graphical avatar rendering.
- Long-running process supervision.
- Real ASR/TTS/vision quality tuning in CI.
- Physical actuation, GPIO, serial, PWM, firmware flashing, or motor control.

## Risks

- Optional packages may have platform-specific install/runtime issues.
- Real microphone/camera permissions cannot be verified in CI.
- Kokoro package APIs may shift; the adapter uses a small compatibility lookup.
- Local model license/checksum hygiene must be maintained before enabling downloads.
