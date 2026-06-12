# Summary: Deterministic Fact Extraction (Stage 1 / M1.2)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `FactExtractor` (`src/android_brain_memory/extraction.py`): deterministic semanticization of structured episode statements (`context["statements"]` with subject/predicate/value) into facts. Facts are always `model_inferred` with confidence capped at 0.75 (`min(episode, statement, cap)`), carry deterministic content-derived IDs (idempotent re-extraction), supporting-episode links, and a `episode → extraction → fact` derivation path; provenance chains reach the raw trace.

Event-driven: the extractor subscribes to `memory_lifecycle` promotion events and extracts automatically when `semantic_candidate` is flagged, publishing `lifecycle_stage="extraction"` events with the report. Conflicts with user-confirmed facts are flagged (`conflicted`), never overwritten. Malformed statements are skipped with reasons.

Combined with M1.1, the lifecycle now runs `observe → buffer → score → promote → semanticize` automatically: a replayed "remember that…" scenario yields a queryable fact with full provenance and zero manual calls.
