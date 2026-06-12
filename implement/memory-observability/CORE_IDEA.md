# Core Idea: Memory Observability (Stage 1 / M1.5)

## Problem Statement

Promotion (M1.1), extraction (M1.2), consolidation (M1.3), and decay (M1.4) already publish `memory_lifecycle` events, but two state changes remain invisible — retrievals and fact conflicts — and there is no CLI way to inspect provenance chains or decay state. The Stage 1 exit criterion requires every memory state change to be traceable from the event stream alone.

## Desired Outcome

- `MnemeMemory` accepts an optional `event_bus`; when present:
  - `retrieve()` publishes a `memory_lifecycle` event (`lifecycle_stage="retrieval"`) with the query metadata, returned IDs, and warnings (never full memory content),
  - `add_fact()` publishes a `memory_lifecycle` event (`lifecycle_stage="conflict"`) whenever an upsert produces a conflict report (covers manual adds and M1.2 extraction alike).
- New CLI commands: `inspect-provenance --memory-id --memory-kind` (provenance chain JSON) and `inspect-decay` (meta-memory records carrying decay metadata).
- New storage read: `get_meta_memory_with_decay(limit)`.

## User / Project Value

The complete lifecycle — promote, extract, consolidate, decay, retrieve, conflict — is now observable on one event stream, and a developer can inspect any memory's derivation and decay state from the shell. This is the debugging substrate every later stage builds on.

## Affected Systems

- `src/android_brain_memory/engine.py`, `storage.py`, `cli.py`
- `tests/test_observability.py` (new)
- `docs/runbooks/MEMORY_CLI.md`, `docs/memory/PROVENANCE.md`, roadmap/status docs

## Assumptions

- Engine-level eventing is opt-in (`event_bus=None` default) so existing callers and the CLI's default path are unchanged.

## Constraints

- Retrieval events carry IDs, counts, and warnings only — no memory content, respecting speakability.
- Deterministic; no new dependencies; no schema changes.

## Non-Goals

- File-based structured logging (the event stream is the log; persistence of events is future work).
- Conflict resolution UI/workflows (Stage 7).

## Risks

- Event payload growth on large retrievals; bounded by `max_results` caps.
