# Local Runtime Events Core Idea

Date: 2026-06-12
Status: Implemented in this feature branch

## Problem

Mneme's design uses ROS-like runtime boundaries, but the V1 repository should remain local, deterministic, and free of ROS runtime requirements. The code needs a lightweight event vocabulary and dispatcher so tests and demos can exercise the intended architecture without introducing middleware complexity.

## Desired Outcome

Add a local compatibility layer for typed runtime events:

- perception observations,
- world/state updates,
- attention updates,
- memory candidates,
- executive intents,
- skill goals/status,
- safety events.

## Project Value

- Prepares code for future ROS-style message boundaries.
- Gives tests and demos a clear way to publish and observe runtime activity.
- Preserves the prime directive that workers publish observations, state builders publish state, the executive publishes intent, skills publish goals/status, and safety may override.

## Constraints

- No ROS 2 integration in this phase.
- No asyncio unless there is a demonstrated need.
- No new dependencies.
- Deterministic ordering for tests.
- Keep memory modules independently testable.

## Non-Goals

- No cross-process transport.
- No durable event log.
- No actuator bridge implementation.
- No hardware-facing behavior.
- No event schema migration.

## Risks

- A generic event bus can blur architecture boundaries if all components use arbitrary event names. The implementation should provide explicit event kinds and helper constructors.
- TTL behavior can become nondeterministic if it depends on sleep. Tests should use explicit timestamps or a fixed clock.
