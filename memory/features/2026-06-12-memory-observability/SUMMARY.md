# Summary: Memory Observability (Stage 1 / M1.5)

Date: 2026-06-12
Type: Feature
Status: Complete — closes Stage 1 of the master roadmap

Completed lifecycle observability:

- `MnemeMemory` accepts an opt-in `event_bus`; `retrieve()` publishes `memory_lifecycle` retrieval events (query metadata, returned IDs, warnings — never memory content) and `add_fact()` publishes conflict events whenever an upsert produces a conflict report (covers manual adds and automatic extraction alike).
- New CLI commands: `inspect-provenance --memory-id --memory-kind` (full chain JSON) and `inspect-decay --limit` (decay-bearing meta-memory records), backed by new `MemoryStore.get_meta_memory_with_decay()`.

With M1.1–M1.4, every memory state change — promotion, extraction, consolidation, decay, retrieval, conflict — is now traceable from the `memory_lifecycle` event stream alone, satisfying the Stage 1 exit criterion. Stage 1 (Autonomous Memory Lifecycle) is complete.
