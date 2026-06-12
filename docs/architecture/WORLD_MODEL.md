# Shared World Model

Status: V1 deterministic world state builder (Stage 2 / M2.1)

`WorldModel` fuses perception events into one typed, TTL-bounded view of "the world right now". It is a state builder: it publishes `world_state_update` events and answers queries; it never publishes intent, skill goals, or safety overrides.

## Inputs

Subscribes to `perception_observation` (observation types `person_seen`, `speech_transcript`, `sound_direction`, `touch`, `body_health`) and `safety_event`.

## State

| State | Type | TTL |
|---|---|---|
| Persons present | `PersonPresence` (id, label, last seen, confidence, expression) | 10 s default |
| Active speaker / last speech | `SpeechActivity` (speaker, transcript, topic) | 6 s default |
| Ambient sound | `SoundState` (direction, label) | 3 s default |
| Last touch | `TouchState` (zone, gesture) | no TTL (latest kept) |
| Internal/body state | `InternalState` (status, battery, safety level) | no TTL (latest kept) |
| Safety level | string from safety events / body health | latest kept |

A speech event also refreshes the speaker's person presence — speakers are persons.

## Outputs

- `world_state_update` events per state change with `state_key` of `persons`, `active_speaker`, `ambient_sound`, `last_touch`, `internal_state`, or `safety_state`. Working memory and attention already consume `active_speaker` and `safety_state` keys.
- `snapshot(now_ms)` → `WorldModelSnapshot`, deterministic (sorted persons, latest-event-wins) and JSON round-trippable.

## Failure / Assumptions

- Unknown observation types are ignored; malformed payloads (missing IDs) are skipped.
- The model trusts event timestamps; expiry is computed against the injected clock.
- Volatile by design: nothing here persists. Durable memory flows through the promotion pipeline.

## Testing

`tests/test_world_model.py`: presence + TTL expiry, speaker tracking + speaker TTL, sound/touch/internal updates, safety level, published state keys, snapshot determinism and JSON round-trip, and a full replay-fixture snapshot.
