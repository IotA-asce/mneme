# Forgetting and Decay

Status: V1 deterministic staged forgetting (Stage 1 / M1.4)

Mneme forgets in stages, never silently and never destructively in V1:

```text
accessibility decay (downranked) -> suppression (hidden, reversible) -> purge (explicit tombstone)
```

## Accessibility Decay (retrieval-time)

Retrieval reads `meta_memory.provenance["decay"]` for every candidate:

- an explicit numeric `downrank` value (clamped to 0..1) is used directly,
- otherwise `accessibility: "downrank_candidate"` (written by consolidation for episodes covered by a summary) applies the default penalty of 0.3,
- otherwise the penalty is 0.

The final score is `weighted_score × (1 − penalty)`. Every ranking explanation includes `decay_penalty` and `score_before_decay`, so downranking is always visible and explainable.

## Suppression (decay pass)

`run_decay_once(store, options, now_s=..., bus=...)` performs one bounded, deterministic pass:

- **Episodes** are suppressed only when *all* hold: active status, decay policy `covered_by_summary`, retrieval count below `min_retrievals_to_keep` (default 1 — any retrieval keeps it), and the reference time (last retrieval, else episode end) older than `suppress_after_s` (default 30 days).
- **Facts** are suppressed only when superseded, not user-confirmed, and older than the threshold (last retrieval, else last confirmation, else first seen).
- `user_confirmed` facts are never auto-suppressed; skips are recorded in the report notes.

Suppressed memories keep their rows, provenance, and support links; ordinary retrieval hides them through the existing active-status default. Restoring is a status change (`set_episode_status` / `set_fact_status`).

Each pass publishes a `memory_lifecycle` event (`lifecycle_stage="decay"`) with the full report, and returns a `DecayReport` (examined/suppressed counts, suppressed IDs, notes).

## Purge (explicit tombstone)

`purge_memory(store, memory_id, kind, reason=..., force=False, now_s=...)`:

- sets status `purged` and writes `provenance["purge"] = {reason, purged_ts, forced}` to meta-memory,
- preserves the row and all provenance — purge is a tombstone, not a deletion,
- requires `force=True` for user-confirmed facts (they are never purged casually),
- is caller-explicit only; nothing schedules purges automatically in V1.

## Non-Goals (V1)

- Detail decay (summarizing content in place) — future work.
- Raw trace retention policy — tracked separately.
- Probabilistic or learned forgetting — everything here is deterministic policy.

## Testing

`tests/test_decay.py` covers downranking order and explanation fields, explicit downrank override, each suppression criterion gating independently, user-confirmed immunity, purge tombstones and the force gate, lifecycle events, status setter validation, and option validation.
