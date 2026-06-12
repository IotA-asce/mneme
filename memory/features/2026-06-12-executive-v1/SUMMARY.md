# Summary: Executive v1 (Stage 2 / M2.4)

Date: 2026-06-12
Type: Feature
Status: Complete

Extended the executive with continuity and memory awareness, all additive and deterministic: a goal stack (`push_goal`/`complete_goal`/`current_goal`) whose active goal rides along on normal-mode intents; safety-driven interruption (freeze/degraded intents suspend active goals) with automatic resumption reported once on recovery; an opt-in response timing gate (`min_response_delay_ms`) that LISTENs with reason `awaiting_turn_completion` until a user turn settles; memory-informed responses (optional `engine`) that retrieve against the user turn — full text first, then deterministic cue-token fallback since storage matches query text as one substring — carrying ID-only memory payloads with `needs_clarification=True` when retrieval warns of conflicting fact records (full bundle on `last_memory_bundle` for the M2.5 dialogue planner); and deterministic idle behavior rotation (ambient_scan/rest_pose/micro_motion).

v0 contracts preserved exactly: defaults reproduce v0; all pre-existing executive tests pass unmodified. Safety rules remain first and unconditional.
