# Stage 6 Local Living Lab — Rules

Date: 2026-06-13
Status: Active

## Architecture Rules

- Local media backends publish observations only.
- The UI visualizes runtime state and submits user input only; it must not own cognition.
- Dialogue produces virtual speech goals; speech output backends publish status through existing skill contracts.
- Command adapters, simulated backends, terminal mode, and JSON mode must remain supported.

## Dependency Rules

- Base install stays lightweight.
- Local audio, VAD, ASR, TTS, and vision packages remain optional extras.
- Tests must use fake devices/models unless explicitly marked manual or opt-in.
- Model files live under `.local/models/` and are not committed.

## Safety Rules

- No physical motor, servo, GPIO, serial, PWM, firmware flashing, or ROS control behavior in Stage 6.
- No direct perception-to-actuator shortcut.
- No unrestricted identity recognition or face embeddings without a specific approved model/license decision.
- Do not treat expression/emotion observations as truth.

## Memory Rules

- Local model-generated observations and memories remain provenance-aware.
- Learned/model-generated memories are `model_inferred` unless the user confirms them.
- Evaluation logs are local artifacts; redact private content before converting them into replay fixtures.

## Testing Rules

- New backends need unit tests with fake devices/models.
- Runtime tests must prove old command/simulated paths still work.
- Real microphone/camera/model checks belong in runbooks until they can be made deterministic.
