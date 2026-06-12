# Local Runtime Event Layer

Status: V1 local compatibility layer  
Date: 2026-06-12

Mneme's long-term runtime should be ROS-like: independent workers publish typed messages, state builders assemble current state, an executive arbitrates intent, skills execute goals, and safety can override behavior.

This repository does not integrate ROS 2 yet. The local runtime layer in `src/android_brain_memory/runtime.py` provides a deterministic in-process event model for tests, demos, replay scaffolding, and future message-boundary alignment.

## Purpose

The runtime layer exists to make architecture boundaries concrete without adding middleware:

- perception workers publish observations,
- world/state builders publish state updates,
- attention publishes focus and salience updates,
- memory publishes candidates,
- the executive publishes intents,
- skills publish goals and status,
- safety publishes safety or degraded-mode events.

The layer is deliberately small and synchronous. It uses standard-library dataclasses and enums only.

## Non-Goals

- No ROS 2 runtime dependency.
- No cross-process transport.
- No actuator bridge.
- No hardware commands.
- No durable event log.
- No background daemon.
- No asyncio event loop.

Asyncio is not used because V1 needs deterministic tests and in-process demos, not concurrent IO. If future runtime work adds network transports, ROS adapters, or long-running workers, async behavior should be introduced at those adapter edges rather than inside the event model.

## Event Shape

All runtime events use `RuntimeEvent`:

- `event_id`: stable event identifier.
- `kind`: one of the runtime event kinds.
- `topic`: derived from `kind` and validated against the architecture boundary.
- `timestamp`: integer timestamp in milliseconds.
- `source`: publishing component name.
- `confidence`: optional probability for uncertain observations, state, attention, intents, or skill status.
- `ttl_ms`: optional time-to-live in milliseconds.
- `sequence`: deterministic local publication order assigned by `EventBus`.
- `payload`: JSON-friendly event data.

Event payloads are intentionally dictionaries for V1. Stable future interfaces can graduate to ROS messages, generated schemas, or stricter typed contracts.

## Event Kinds

`RuntimeEventKind` contains:

- `perception_observation`
- `world_state_update`
- `attention_update`
- `memory_candidate`
- `executive_intent`
- `skill_goal`
- `skill_status`
- `safety_event`

Helper constructors exist for each category:

- `perception_observation(...)`
- `world_state_update(...)`
- `attention_update(...)`
- `memory_candidate_event(...)`
- `executive_intent(...)`
- `skill_goal(...)`
- `skill_status(...)`
- `safety_event(...)`

## Event Bus

`EventBus` is a synchronous dispatcher:

- `subscribe(callback, kinds=..., topics=..., sources=...)`
- `unsubscribe(subscription_id)`
- `publish(event)`
- `history(...)`
- `expire(now_ms=...)`

Publication is immediate and deterministic. Subscribers are called in subscription insertion order. Events receive monotonically increasing `sequence` values when published.

Expired events are recorded in history but are not delivered to subscribers. `history(include_expired=False, now_ms=...)` hides expired events, and `expire(now_ms=...)` prunes them from local history.

## Boundary Rules

The bus must not become a shortcut around the architecture:

- Perception events must not command skills or actuators.
- Memory candidate events must not represent executive decisions.
- Executive intent is not an actuator command.
- Skill goal/status events are not final actuator bridge commands.
- Safety events are local coordination signals, not a certified hardware safety supervisor.

Future ROS integration should map these event kinds to ROS messages or topics while preserving the same authority boundaries.

## Deterministic Testing

Tests should pass explicit timestamps or inject a fixed bus clock:

```python
bus = EventBus(clock=lambda: 1000)
```

Avoid sleep-based tests. TTL behavior should be checked by passing `now_ms` to `history()` or `expire()`.

## Current Limitations

- No persistence of runtime event history.
- No backpressure or queue depth policy.
- No wildcard payload schema validation beyond JSON-friendly mappings.
- No bridge to existing `interfaces/` files yet.
- No summary or observability dashboard.

These limitations are intentional for V1. The layer is a compatibility and testing scaffold, not the final runtime.
