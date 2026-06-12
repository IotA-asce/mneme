# Summary: Shared World Model (Stage 2 / M2.1)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `WorldModel` (`src/android_brain_memory/world_model.py`): a deterministic state builder fusing perception events into typed, TTL-bounded world state — persons present (10s TTL, refreshed by both face and speech events), active speaker + last speech (6s TTL), ambient sound (3s TTL), last touch, internal/body state, and safety level. Publishes `world_state_update` events per state change (state keys: persons, active_speaker, ambient_sound, last_touch, internal_state, safety_state), which working memory and attention already consume. Snapshots are deterministic, sorted, and JSON round-trippable.

Strictly a state builder: no intent, no skill goals, no safety origination, no persistence.
