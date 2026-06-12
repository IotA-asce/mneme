# Context

Roadmap Phase 1 (storage and provenance baseline) was intentionally skipped while Phases 2–5 were built, leaving writes without their matching reads:

- raw traces could be written but not read back,
- `fact_support` rows could only be observed indirectly through `Fact.supporting_episode_ids`,
- episodes had no time-window query,
- provenance pieces (meta-memory `supporting_memory_ids`, support links) could not be walked end-to-end.

The roadmap named this gap the "current safest next task" before expanding retrieval behavior further, because retrieval warnings and provenance summaries in bundles (Phase 4 leftovers) depend on these reads existing.

Design decisions:

- Overlap semantics for the episode window (`start_ts <= window_end AND end_ts >= window_start`) so episodes spanning a boundary are included.
- Traversal reports missing references instead of failing, because echo-only traces legitimately expire without being persisted.
- `summary` memory kind included in chain resolution so consolidation outputs are traversable too.
- Breadth-first, visited-set traversal with sorted reference order for determinism.
