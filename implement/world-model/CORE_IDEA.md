# Core Idea: Shared World Model (Stage 2 / M2.1)

## Problem Statement

There is no fused, typed view of "the world right now". Perception events flow to working memory, attention, and the executive independently, each re-deriving fragments (who is present, who is speaking) from raw payloads. Nothing owns persons-present, ambient sound, last touch, or robot internal state as queryable state with TTLs.

## Desired Outcome

A `WorldModel` state builder that consumes `perception_observation` (and `safety_event`) runtime events and maintains typed state: persons present (with TTL), active speaker (with TTL), last speech, ambient sound (with TTL), last touch, internal/body state, and safety level. It publishes `world_state_update` events per state change (which working memory and attention already consume) and produces deterministic, JSON-friendly snapshots.

## User / Project Value

One authoritative "now" that downstream cognition (working memory windows in M2.2, attention in M2.3, executive in M2.4) can query instead of re-parsing perception payloads. Snapshot-testable under replay.

## Affected Systems

- `src/android_brain_memory/world_model.py` (new), `__init__.py`
- `tests/test_world_model.py` (new)
- `docs/architecture/WORLD_MODEL.md` (new), RUNTIME.md cross-ref, roadmap/status docs

## Assumptions

- Observation types match the simulated workers: `person_seen`, `speech_transcript`, `sound_direction`, `touch`, `body_health`.
- Speakers are persons: a speech event also refreshes that person's presence.

## Constraints

- State builder only: publishes `world_state_update`, never intent/goals/safety overrides. Deterministic, injected clock, no threads, stdlib only.

## Non-Goals

- Object tracking, spatial maps, multi-camera fusion (Stage 4 brings real perception fusion).
- Persistence (the world model is volatile runtime state; episodes/facts persist separately).

## Risks

- Event ordering matters; mitigated by monotonic timestamps and deterministic tie handling (latest event wins per state key).
