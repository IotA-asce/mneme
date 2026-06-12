# Summary: Automatic Memory Promotion Pipeline (Stage 1 / M1.1)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `MemoryPromoter` (`src/android_brain_memory/promotion.py`): a runtime component that subscribes to `memory_candidate` events, scores each candidate with the existing salience machinery, and maps the decision to storage automatically — `echo_only` (nothing durable), `working_memory_candidate` (raw trace), `episode` (trace + episode), `episode_and_semantic_candidate` (trace + episode + semantic flag for the M1.2 extractor). Storage delegates to `MnemeMemory.remember_candidate` so provenance/meta-memory behavior is unchanged.

Added a ninth runtime event kind, `memory_lifecycle` (topic `memory`), with a `memory_lifecycle_event()` helper — the observability channel for all Stage 1 lifecycle components. Every promotion publishes one with candidate ID, decision, score, and stored IDs. Malformed candidate events are counted and skipped, never raised.

Stage 1 exit criterion for M1.1 met: replaying `basic_conversation.yaml` with a promoter attached produces a durable episode whose provenance chain reaches the raw trace, with zero manual storage calls.
