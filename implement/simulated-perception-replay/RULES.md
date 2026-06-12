# Simulated Perception Replay Rules

Date: 2026-06-12
Status: Implemented in this feature branch

## Architecture Rules

- Simulated workers publish observations only.
- Replay must use the local `EventBus`.
- Working memory and sensory echo must update through subscriptions, not direct mutation.
- Memory candidates must be explicit in the scenario or intentionally marked important.

## Safety Rules

- Do not add real sensor integration.
- Do not add actuator behavior.
- Do not imply simulated health or safety events are certified safety enforcement.
- Do not store secrets in scenario fixtures.

## Testing Rules

- Use deterministic timestamps.
- Use local fixtures.
- Assert event order, working-memory state, echo contents, and memory candidate emission.

## Anti-Patterns

- No OpenCV, Whisper, audio libraries, ROS, or asyncio.
- No background threads.
- No hidden LLM or ML inference.
- No unbounded replay logs.
