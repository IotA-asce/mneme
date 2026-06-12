# Summary: Forgetting and Decay Policy (Stage 1 / M1.4)

Date: 2026-06-12
Type: Feature
Status: Complete

Implemented staged, deterministic forgetting:

1. **Accessibility decay**: retrieval now multiplies scores by `(1 - decay_penalty)` read from meta-memory decay metadata — explicit `downrank` values win, consolidation's `downrank_candidate` hint applies 0.3 — with `decay_penalty` and `score_before_decay` in every ranking explanation.
2. **Suppression**: `run_decay_once()` suppresses episodes that are summarized (`covered_by_summary`), unretrieved (count below keep threshold), and older than 30 days (configurable), plus old superseded non-user-confirmed facts. Reversible (status change only), bounded, reported, and published as `memory_lifecycle` decay events.
3. **Purge**: `purge_memory()` is an explicit provenance-preserving tombstone (status `purged` + reasoned purge note in meta provenance). User-confirmed facts require `force=True`.

Storage gained public `set_episode_status` / `set_fact_status` setters with `KeyError` validation. User-confirmed facts are never auto-suppressed; nothing is deleted in V1.
