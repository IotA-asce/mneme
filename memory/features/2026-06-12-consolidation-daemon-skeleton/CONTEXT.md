# Context

The design document describes consolidation as an idle/background job that clusters similar episodes, creates summaries, extracts facts, detects contradictions, and prunes or downranks low-value items.

Before this change, `consolidate_once()` was intentionally non-mutating. The storage layer already had `memory_summary` and meta-memory provenance support, making it possible to implement a narrow summary-producing pass without a schema migration.

This feature intentionally keeps consolidation deterministic and local. It creates summaries and records decay hints, but leaves fact extraction, contradiction handling, summary retrieval, and scheduling for later phases.
