# Attention Manager v0

The Attention Manager is Mneme's local runtime component for deciding what currently matters. It consumes runtime events and publishes attention state through `RuntimeEventKind.ATTENTION_UPDATE`.

It does not command gaze, speech, servos, motors, or other actuators. Future skills can consume attention state and decide whether movement is appropriate.

## Inputs

The manager listens to:

- perception observations such as speech transcripts, person sightings, sound direction, touch, and visible objects
- world-state updates such as active speaker or active goal
- executive intents and skill goals that indicate the current goal context
- safety events

## Outputs

The manager publishes an `attention_update` event containing:

- active `focus_id`
- serialized `AttentionState`
- serialized active `AttentionTarget`
- priority and reason

Working memory can consume this event and update its `attention_target` field.

## Target Model

`AttentionTarget` represents one candidate focus item:

- `target_id`: stable local ID such as `person:user`, `sound:unknown:90`, or `safety:degraded`
- `target_type`: broad type such as `person`, `sound`, `touch`, `object`, `goal`, or `safety`
- `label`: human-readable label
- `last_event_id` and `last_seen_ts`
- `confidence`
- `priority`
- `factors`: normalized feature values
- `weighted_components`: priority contribution by feature
- `ttl_ms` and `expires_at`

`AttentionState` captures the active target, ranked candidates, dwell lock timing, and the selection reason.

## Priority Factors

V0 uses deterministic scoring with these factors:

- active speaker
- sound event
- face/person presence
- explicit user address, such as a transcript mentioning "Mneme"
- safety relevance
- novelty
- current goal match
- confidence

The explanation is stored on each target as raw factors and weighted components. Safety relevance has an override path so degraded or critical safety events are not treated as ordinary social focus.

## Dwell And Expiry

The manager uses a short dwell lock after selecting a target. This prevents rapid flicker between similar targets. A materially higher-priority target or safety-relevant target can still replace the current target.

Targets expire after their TTL. Expired active targets are released rather than kept as stale focus.

## Runtime Boundary

Attention is a state builder, not a skill:

```text
perception/world/safety events -> AttentionManager -> attention_update
```

The next layer may use attention state to plan gaze or dialogue, but this module deliberately stops before motor intent.

## Verification

Covered behavior includes:

- active speaker outranking idle objects
- safety events outranking normal social focus
- dwell lock preventing rapid flicker
- expired targets being released
- JSON round trips for attention state
