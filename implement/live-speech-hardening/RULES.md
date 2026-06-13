# Live Speech Hardening Rules

## Architecture

- Speech diagnostics may observe runtime events but must not choose dialogue, mutate memory, or command skills.
- Perception remains the owner of transcript observations.
- Executive/dialogue remain the owner of response intent and wording.
- Virtual skills remain the owner of speech output status.
- Physical hardware remains out of scope.

## Testing

- CI tests must use fake devices and fake ASR/TTS backends.
- Real microphone, ASR model, TTS playback, and speaker routing are manual acceptance tasks.
- Speech soak fixtures must be deterministic and local.

## Failure Behavior

- Missing microphone, no speech, ASR error, TTS failure, duplicate suppression, barge-in, and stuck speaking must be represented in JSON.
- TTS failure must not erase the deterministic dialogue plan; it should fail the speech skill and leave diagnostics visible.
- Duplicate suppression applies to live/external speech turns, not typed input.

## Anti-Patterns

- Do not add a second speech pipeline parallel to the runtime.
- Do not let ASR/TTS code bypass executive intent or dialogue planning.
- Do not add required media/model dependencies to the base install.
- Do not treat fake-backed soak success as proof of real-device quality.
