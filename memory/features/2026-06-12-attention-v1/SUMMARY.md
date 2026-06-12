# Summary: Attention Manager v1 (Stage 2 / M2.3)

Date: 2026-06-12
Type: Feature
Status: Complete

Extended `AttentionManager` with four deterministic, additive v1 behaviors: habituation (per-target exposure counts decay novelty geometrically: 1.0 → 0.5 → 0.25 → …), inhibition of return (a windowed priority penalty — default 0.15 for 2s — on targets focus just left, surfaced as an explicit `inhibition_of_return` factor; safety targets immune), opt-in idle curiosity (`enable_curiosity=True` + `idle_tick()` rotate synthetic scan_left/scan_center/scan_right targets at priority 0.05 that any real target preempts), and a bounded `state_history` of focus transitions for explainability.

v0 contracts preserved exactly: curiosity is opt-in because v0 promises a None active target when idle; all pre-existing attention tests pass unmodified.
