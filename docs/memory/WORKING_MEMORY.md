# Sensory Echo and Working Memory

Status: V1 local runtime memory components  
Date: 2026-06-12

Mneme's early memory lifecycle starts before durable storage:

```text
runtime event -> sensory echo -> working memory context -> score/promote/retrieve
```

This document describes the local V1 components in `src/android_brain_memory/working_memory.py`. They are bench-only, deterministic, and integrated with the local runtime `EventBus`. They do not start ROS 2, use cameras or microphones, control hardware, or promote memories automatically.

## Sensory Echo Buffer

`SensoryEchoBuffer` stores short-lived `EchoFragment` records derived from runtime events.

Each fragment keeps:

- fragment ID,
- source event ID,
- event kind,
- timestamp,
- source,
- confidence when present,
- TTL in milliseconds,
- expiration time,
- runtime sequence,
- JSON-friendly payload.

The buffer is bounded by:

- `capacity`,
- `default_ttl_ms`,
- explicit expiry checks.

If a runtime event has its own `ttl_ms`, that TTL is used. Otherwise the buffer's `default_ttl_ms` is applied. Expired fragments are not added and can be pruned with `expire(now_ms=...)`.

The buffer can subscribe to the runtime bus:

```python
echo = SensoryEchoBuffer(capacity=64, default_ttl_ms=5000)
echo.attach_to_bus(bus, sources=["vision_worker", "speech_worker"])
```

## Working Memory

`WorkingMemory` maintains a small explicit active context:

- current speaker,
- current topic,
- attention target,
- recent dialogue turns,
- active goal,
- safety state,
- pending response intent,
- recent runtime event references.

It is not a chat history, durable event log, or semantic memory. It has explicit caps:

- `max_dialogue_turns`,
- `max_event_refs`.

When caps are exceeded, the oldest entries are dropped.

## Event Bus Updates

Working memory can subscribe to `EventBus`:

```python
working = WorkingMemory(max_dialogue_turns=8, max_event_refs=16)
working.attach_to_bus(bus)
```

Handled event kinds:

- `perception_observation`: may update current speaker, topic, and recent dialogue turns.
- `world_state_update`: may update active speaker, topic, or safety context.
- `attention_update`: updates attention target and optional topic.
- `executive_intent`: updates pending response intent and optional active goal.
- `skill_goal`: updates active goal.
- `skill_status`: records status under the active goal.
- `safety_event`: updates safety state.

Payloads are still V1 JSON dictionaries. Common keys are documented by tests and examples rather than a generated schema.

## Snapshot Export

Use `snapshot()` or `to_dict()` to export JSON-friendly active context:

```python
snapshot = working.snapshot(created_ts=1000)
payload = snapshot.to_dict()
```

Snapshots include only bounded working-memory state. They do not include the entire event bus history or sensory echo contents.

## Optional Persistence

`WorkingMemory.persist_snapshot(store)` writes the snapshot through the existing storage API:

```python
stored = working.persist_snapshot(store, snapshot_id="ctx_001", created_ts=1000)
```

This writes to `working_context_snapshot`. It does not create episodes, facts, summaries, or raw traces.

## Boundary Rules

- Sensory echo is temporary and selective.
- Working memory is active context, not durable memory.
- Memory components observe events but do not command actuators.
- Safety state is context for coordination, not certified safety enforcement.
- No real camera, microphone, GPIO, serial, servo, or motor integration exists in this phase.

## Testing

Use explicit timestamps or injected clocks. Avoid sleep-based expiry tests.

Targeted tests:

```bash
python -m pytest tests/test_working_memory.py
```

The tests cover:

- echo TTL expiry,
- echo capacity limits,
- event bus subscription filters,
- working-memory bounded dialogue and event references,
- context updates from runtime events,
- snapshot export,
- snapshot persistence to SQLite.

## Context Windows (Lifecycle v1)

`ContextWindowManager` bounds interactions into context windows:

- a window **opens** when an interaction-relevant perception event arrives (`speech_transcript`, `person_seen`, `touch`) and no window is open,
- continued interaction events refresh the window's last-activity time and event count,
- `tick(now_ms)` **closes** the window after `idle_timeout_ms` (default 8s) of inactivity; `close_now(reason=...)` closes it explicitly (e.g. on safety freeze),
- at the close boundary a working-memory snapshot is **persisted automatically** through `WorkingMemory.persist_snapshot()` and the window records its `snapshot_id`,
- closed windows are kept in a bounded history; transitions publish `world_state_update` events with `state_key="context_window"` and `status` of `opened`/`closed`.

One window at a time in V1; overlapping interactions extend the current window. The manager owns lifecycle only — content updates remain in `WorkingMemory`. Like the consolidation daemon, `tick()` is caller-driven with an injected clock (no threads).

## Future Work

- Add explicit adapters from runtime events to future ROS messages.
- Bridge closed context windows into episodic encoding (window → episode candidate).
- Multi-party concurrent windows.
