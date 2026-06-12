# Stage 5 Conversational Presence Rules

## Architecture Boundaries

- Perception workers publish observations.
- Working/world/attention layers publish state.
- The executive publishes intent.
- The dialogue planner produces utterance plans.
- The Stage 5 coordinator maps intent/plans to virtual skill goals.
- The virtual skill runner publishes skill status.
- No Stage 5 component commands physical actuators.

## Safety Constraints

- Local TTS command failures become failed virtual skill status, not hardware commands.
- Barge-in preempts virtual speech only; it does not command motion.
- Safety events cancel active virtual skills and move avatar state to safety mode.
- Simulated success must not be described as physical safety verification.

## Testing Expectations

- Use injected clocks for timing.
- Use simulated speech by default.
- Test command adapters with injected command runners or harmless local commands.
- Assert status event ordering and JSON snapshot shape.
- Preserve Stage 3 and Stage 4 runtime tests.

## Persistence Rules

- Speech voice is stored as procedural memory under `procedure:speech:voice`.
- Reusing the same voice should not create unnecessary versions.
- Speech output text is observable in runtime JSON; do not store secrets in command metadata.

## Anti-Patterns

- Direct dialogue-planner-to-TTS calls.
- Perception-to-speech shortcuts.
- Native media dependencies in the base package.
- GUI state that bypasses avatar snapshots.
- Any GPIO, serial, PWM, firmware, motor, or ROS control code in Stage 5.
