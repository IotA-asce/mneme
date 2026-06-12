# Changes

- Added `AttentionTarget` and `AttentionState` dataclasses.
- Added `AttentionManager` with deterministic scoring, target TTL expiry, dwell lock behavior, and safety override handling.
- Published attention state through existing `attention_update` runtime events.
- Exported attention models from the package.
- Added tests for social focus, safety override, dwell lock, expiry, and serialization.
- Documented boundaries in `docs/attention/ATTENTION_MANAGER.md`.
