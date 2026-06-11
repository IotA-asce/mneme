# Provenance and Meta-Memory Integration

Type: Feature
Date: 2026-06-11
Status: Complete

## Summary

Added first-class provenance and meta-memory integration for stored memory records:

- raw traces, episodes, facts, and summaries can write corresponding meta-memory records,
- provenance JSON is normalized around source type, source ID, derivation path, supporting memory IDs, and optional notes,
- secret-like provenance keys are rejected before storage,
- retrieval updates `retrieval_count` and `last_retrieved_ts` for returned facts and episodes,
- speakability now has typed values: `normal`, `restricted`, `never_say`, and `internal_only`,
- ordinary retrieval hides `never_say` and `internal_only` records unless explicitly requested by a trusted internal query.

No encryption, vector search, LLM policy decisions, or new dependencies were added.
