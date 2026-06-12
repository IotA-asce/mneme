# Implementation Plan

## Phase 1 — Typed State + WorldModel

- `world_model.py`: `PersonPresence`, `SpeechActivity`, `SoundState`, `TouchState`, `InternalState`, `WorldModelSnapshot` dataclasses (validated, `to_dict()`), and `WorldModel`:
  - `attach_to_bus` subscribing to `perception_observation` + `safety_event`,
  - dispatch by `observation_type` (`person_seen`, `speech_transcript`, `sound_direction`, `touch`, `body_health`),
  - speech refreshes the speaker's person presence,
  - TTL expiry for persons / active speaker / ambient sound (`expire(now_ms)`),
  - `world_state_update` publication per state change (`persons`, `active_speaker`, `ambient_sound`, `last_touch`, `internal_state`, `safety_state`),
  - `snapshot(now_ms)` returning a deterministic `WorldModelSnapshot`.

## Phase 2 — Tests (written first)

- `tests/test_world_model.py`: person presence + TTL expiry, speech → active speaker + person refresh + speaker TTL, sound/touch/internal updates, safety level, published `world_state_update` events with correct state keys, JSON-stable snapshots, full replay-fixture snapshot.

## Phase 3 — Docs

- `docs/architecture/WORLD_MODEL.md` (new), `MASTER_ROADMAP.md` M2.1, `REPO_STATUS.md`, memory entry + index.

## Validation

- `python -m pytest tests/test_world_model.py` then full suite + dev_check.

## Rollback

Revert new module/tests/docs. No schema or behavior changes elsewhere.

## Definition of Done

World state queryable and snapshot-testable under replay; state changes published as `world_state_update` events consumed by existing components; full suite passes.
