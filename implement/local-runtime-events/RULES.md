# Local Runtime Events Rules

Date: 2026-06-12
Status: Implemented in this feature branch

## Runtime Boundaries

- Perception workers publish observations.
- State builders publish world/state updates.
- Attention publishes focus/salience updates.
- Memory publishes candidates; it does not command behavior.
- Executive publishes intents.
- Skills publish goals and status.
- Safety publishes override/degraded-mode events and may be observed by any layer.

## Safety Constraints

- Events must not send actuator commands directly.
- This local layer must not imply hardware safety.
- Safety events are coordination signals, not a safety-certified supervisor.

## Determinism

- Publication order is assigned by a local sequence counter.
- Tests must use explicit timestamps or a deterministic clock.
- TTL expiry is checked against a provided timestamp, not sleeps.

## Anti-Patterns

- Do not add ROS imports.
- Do not add asyncio for simple in-process publication.
- Do not treat the bus as a global singleton.
- Do not use stringly-typed event categories when an enum exists.
- Do not store secrets in event payloads.
