# Core Idea: Storage and Provenance Read APIs

## Problem Statement

Storage writes raw traces, fact support links, and meta-memory provenance, but the read side is incomplete:

- raw traces cannot be read back by ID or listed,
- fact support links cannot be read directly,
- episodes cannot be queried by time window,
- the stored provenance pieces (trace, episode, fact support, meta-memory) cannot be traversed end-to-end.

This blocks the roadmap Phase 1 exit criteria: a stored candidate must be traceable from raw trace to episode to fact support.

## Desired Outcome

- `MemoryStore` exposes deterministic read APIs for raw traces and fact support links.
- Episodes can be retrieved by overlapping time window.
- A provenance chain can be generated for a fact, episode, or raw trace from already-stored data.
- No schema changes and no new dependencies.

## User / Project Value

Stored memories become inspectable and auditable. Future retrieval, consolidation, and review tooling can explain where a memory came from instead of trusting opaque rows.

## Affected Systems

- `src/android_brain_memory/storage.py` (new read methods, two read-model dataclasses)
- `tests/` (new test module)
- `docs/memory/STORAGE.md`, `docs/memory/PROVENANCE.md`
- `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`

## Assumptions

- Existing `raw_trace`, `fact_support`, `episode`, and `meta_memory` tables already hold the needed data.
- Provenance references stored in meta-memory `supporting_memory_ids` use memory IDs (`trace_*`, `ep_*`, fact IDs).
- Referenced IDs may be missing (e.g. echo-only traces that were never persisted); traversal must report them, not fail.

## Constraints

- Standard library only.
- Deterministic ordering and tie-breaks for all list reads.
- Read-only: no writes, no migrations, no mutation of provenance during traversal.

## Non-Goals

- Retrieval-bundle integration of provenance summaries (Phase 4 work).
- Fact extraction, decay, or consolidation changes.
- CLI surface changes.
- Cycle-heavy graph analytics; traversal only needs bounded, cycle-safe walking.

## Risks

- Provenance data written before this change may have sparse `supporting_memory_ids`; traversal output will be shallow for old rows (acceptable: report what exists).
- Time-window semantics could be ambiguous; we standardize on overlap (episode.start_ts <= window_end AND episode.end_ts >= window_start).
