# Repository Status

Date: 2026-06-12
Status: V1 starter memory prototype audit

This audit records what the repository actually implements today versus what the design documents describe for the broader Mneme architecture.

## Current Implementation

The repository currently implements a local, bench-only Python memory prototype. It does not control hardware, run ROS 2 nodes, use a vector database, call LLM services, or process real camera/audio streams.

Implemented foundations:

- Python package metadata in `pyproject.toml` for `android-brain-memory`.
- SQLite schema migration in `storage/migrations/001_init.sql`.
- Developer scripts for database initialization and a memory smoke path.
- ROS-style interface drafts under `interfaces/`; these are documentation/contract drafts, not generated runtime bindings.
- Project documentation, starter prompts, configuration, and architecture diagrams.
- Local runtime event types and an in-process event bus for ROS-like test/demo boundaries without requiring ROS.
- Bounded sensory echo and working-memory runtime components that can subscribe to local runtime events.
- Deterministic simulated perception workers and YAML/JSON scenario replay for local tests and demos.

Implemented memory code:

- Dataclass models for `MemoryCandidate`, `SalienceFeatures`, `SalienceResult`, `Episode`, `Fact`, `MemoryQuery`, and `MemoryBundle`.
- Source and status enums for source provenance and memory lifecycle state.
- Weighted salience scoring using built-in defaults or `config/memory.yaml`.
- Salience explanation payloads with feature values, weighted components, thresholds, and override reasons.
- Promotion decisions for echo-only, working-memory candidate, episode, and episode-plus-semantic-candidate.
- Explicit remember override when `explicit_remember_flag >= 0.9`.
- SQLite connection management and migration application through `MemoryStore`.
- Migration tracking through `schema_migration`, including migration IDs, filenames, checksums, and applied timestamps.
- Writes for raw traces, episodes, and facts.
- Fact support link writes through `fact_support`.
- Fact tag persistence through `fact_tag`.
- Meta-memory record writes, reads, and partial updates.
- Meta-memory writes during raw trace, episode, fact, and summary storage.
- Meta-memory retrieval count and last-retrieved timestamp updates when retrieval returns facts or episodes.
- Speakability filtering for `never_say` and `internal_only` records during ordinary retrieval.
- Working context snapshot writes and recent snapshot reads.
- Active working-memory context tracking for current speaker, topic, attention target, recent dialogue turns, active goal, safety state, and pending response intent.
- Memory summary writes.
- Fact and episode lookup by ID.
- Free-text and structured fact search over subject, predicate, object text, source type, status, and tags.
- Basic free-text episode search over summary and JSON context.
- Basic `retrieve_memory()` bundle creation over facts and episodes.
- Include flags for suppressing fact or episode retrieval.
- Default active-only fact retrieval with explicit non-active status queries for review/debug flows.
- User-confirmed facts outrank inferred facts when relevance is otherwise similar.
- Deterministic retrieval reranking over facts and episodes using context match, entity match, recency, salience, confidence, source reliability, and meta-memory retrieval history where available.
- `MemoryBundle.ranking_explanations` debug output for returned ranked items.
- A deterministic `consolidate_once()` skeleton that groups repeated episodes, creates summaries, preserves episodes, and writes decay/downranking metadata to meta-memory.
- `open_default_store()` helper pointing at `.local/android_brain_memory.sqlite3`.
- High-level `MnemeMemory` / `MemoryEngine` facade for migration initialization, candidate scoring, raw trace storage, episode encoding/storage, fact upsert, retrieval, one-shot consolidation, and database inspection.
- JSON-oriented memory CLI with `init-db`, `remember-candidate`, `add-episode`, `add-fact`, `retrieve`, `consolidate-once`, and `inspect-db` commands.
- Runtime event helpers for perception observations, world/state updates, attention updates, memory candidates, executive intents, skill goals/status, and safety events.
- Scenario replay runner that publishes simulated face/person, speech transcript, sound direction, touch, and body/internal health events through the local runtime bus.

## Partially Implemented

The following areas exist but are not complete enough to count as full phase completion:

- Sensory echo: `raw_trace` exists and can be written, but there is no read-by-id/list API, no retention policy, and no promotion pipeline that starts from raw traces.
- Working memory: `WorkingMemory` maintains a bounded active context and can export/persist snapshots. There is no autonomous promotion pipeline or long-running working-memory daemon yet.
- Episodic memory: episodes can be written, found by text, and retrieved by ID. Participant and object entities are persisted through `episode_entity`. There is no time-window query, topic-specific query API, first-class persisted episode provenance list, or dedicated episode debug output.
- Provenance: source type, confidence, fact support links, normalized meta-memory provenance JSON, retrieval counters, speakability, and caller-provided trace references exist in pieces. There is no end-to-end provenance traversal, version history, or persisted episode provenance list.
- Semantic facts: facts can be upserted, source typed, tagged, searched by structured fields, linked to supporting episodes, checked for conservative semantic conflicts, marked `superseded`/`conflicted`, and queried through conflict reports.
- Retrieval manager: retrieval returns reranked facts and episodes from local SQLite, updates meta-memory retrieval history for returned records, and filters internal-only speakability records by default. It does not search working memory, summaries, or self model.
- Consolidation: a one-shot deterministic pass can create repeated-episode summaries and meta-memory decay hints. No long-running daemon, fact extraction, contradiction review, purge behavior, or retrieval downranking is implemented.
- Meta-memory: typed storage methods exist for records, provenance JSON, speakability, and retrieval history updates.
- Config: `config/memory.yaml` records salience defaults that can be loaded when requested.

## Documented But Not Implemented

The design documents describe these future capabilities, but the repository does not yet implement them:

- Real perception workers for vision, speech, sound direction, touch, body state, or internal health.
- Shared world model, attention manager, executive arbiter, skill controllers, actuator bridge, and safety supervisor.
- Physical actuator control or dry-run hardware backend.
- Full ROS 2 package/runtime integration.
- Long-running memory daemon or background process.
- Promotion pipeline from observation to buffer to scoring to storage.
- Working memory lifecycle and active context management.
- Procedural memory and self model behavior.
- Semanticization of repeated episodes into facts.
- Forgetting, accessibility decay, detail decay, and purge policy beyond current speakability filtering and consolidation decay metadata.
- Contradiction review or supersession workflow.
- Structured observability logs for promotion decisions, retrieval rankings, consolidation changes, conflicts, and pruning.
- Full JSON-friendly serialization contract for future ROS wrappers.

## Current Tests

The test suite currently contains focused model, salience, storage, and retrieval tests, including:

- `tests/test_salience.py::test_explicit_remember_promotes_to_semantic_candidate`
- `tests/test_salience.py::test_low_salience_echo_only`
- `tests/test_storage_retrieval.py::test_store_trace_episode_and_fact_then_retrieve_bundle`
- `tests/test_storage_retrieval.py::test_retrieve_memory_respects_fact_and_episode_include_flags`
- `tests/test_storage_retrieval.py::test_structured_fact_retrieval_by_subject`
- `tests/test_storage_retrieval.py::test_structured_fact_retrieval_by_predicate`
- `tests/test_storage_retrieval.py::test_structured_fact_retrieval_by_object_text_and_tags`
- `tests/test_storage_retrieval.py::test_user_confirmed_facts_outrank_inferred_facts_when_relevance_is_similar`
- `tests/test_storage_retrieval.py::test_structured_fact_retrieval_filters_status_by_default_and_explicit_status`
- `tests/test_storage_retrieval.py::test_reranking_orders_episodes_deterministically_and_explains_factors`
- `tests/test_storage_retrieval.py::test_retrieval_history_bonus_reranks_similar_facts_and_is_explained`
- `tests/test_storage_migrations.py::test_migrations_are_tracked_and_idempotent`
- `tests/test_storage_migrations.py::test_migration_checksum_mismatch_is_rejected`
- `tests/test_storage_migrations.py::test_meta_memory_write_read_and_update_preserves_fields`
- `tests/test_storage_migrations.py::test_working_context_snapshots_are_read_recent_first`
- `tests/test_storage_migrations.py::test_get_episode_and_fact_by_id_preserve_typed_fields`
- `tests/test_storage_migrations.py::test_user_confirmed_fact_supersedes_inferred_conflict`
- `tests/test_storage_migrations.py::test_user_confirmed_fact_conflict_preserves_both_for_review`
- `tests/test_storage_migrations.py::test_same_semantic_fact_duplicate_is_not_a_conflict`
- `tests/test_storage_migrations.py::test_context_preserving_fact_difference_is_not_a_conflict`
- `tests/test_consolidation.py::test_consolidate_once_creates_summary_for_repeated_episodes`
- `tests/test_memory_engine_cli.py::test_mneme_memory_facade_conversation_like_flow`
- `tests/test_memory_engine_cli.py::test_memory_cli_conversation_like_flow_outputs_json`
- `tests/test_runtime_events.py::test_event_publication_subscription_and_ordering`
- `tests/test_runtime_events.py::test_subscription_filters_by_kind_topic_and_source`
- `tests/test_runtime_events.py::test_expired_events_are_not_delivered_and_can_be_pruned`
- `tests/test_runtime_events.py::test_all_required_runtime_event_types_are_json_friendly`
- `tests/test_runtime_events.py::test_event_validation_rejects_invalid_confidence_and_mismatched_topic`
- `tests/test_working_memory.py::test_sensory_echo_buffer_expires_fragments_and_respects_capacity`
- `tests/test_working_memory.py::test_sensory_echo_buffer_subscribes_to_event_bus_with_filters`
- `tests/test_working_memory.py::test_working_memory_updates_from_runtime_events_and_stays_bounded`
- `tests/test_working_memory.py::test_working_memory_records_world_state_and_skill_goal_status`
- `tests/test_working_memory.py::test_working_memory_snapshot_persists_to_storage`
- `tests/test_scenario_replay.py::test_loads_basic_conversation_scenario`
- `tests/test_scenario_replay.py::test_replay_basic_conversation_updates_echo_working_memory_and_candidates`
- `tests/test_scenario_replay.py::test_json_scenario_replay_matches_yaml_shape`

Coverage is focused on model validation, salience decisions, raw trace/episode/fact/summary writes, migration tracking, meta-memory storage, provenance normalization, speakability filtering, retrieval history updates, working context snapshots, structured fact retrieval, deterministic retrieval reranking, semantic fact conflict handling, basic episode retrieval, repeated-episode consolidation summaries, consolidation decay metadata, retrieval include flags, the high-level memory API/CLI conversation-like flow, local runtime event publication/subscription behavior, bounded sensory echo/working-memory behavior, and deterministic scenario replay. There are no tests yet for full provenance traversal, fact extraction from consolidation, retrieval use of decay/downranking, raw trace read APIs, time-window episode queries, ROS adapters, cross-process runtime behavior, real sensor workers, or autonomous promotion from working memory.

## Verification Commands

Recommended clean local verification:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/init_db.py
python scripts/smoke_test_memory.py
python scripts/mneme_memory.py inspect-db
python -m pytest
```

When the package is not installed but dependencies are already present, scripts can also be run with:

```bash
PYTHONPATH=src python3 scripts/init_db.py
PYTHONPATH=src python3 scripts/smoke_test_memory.py
PYTHONPATH=src python3 scripts/mneme_memory.py inspect-db
PYTHONPATH=src python3 -m pytest
```

There is no configured lint, typecheck, formatter, or build command beyond package installation and tests.

## Safest Next Tasks

The safest next tasks should stay inside the memory prototype and avoid hardware, ROS runtime, new dependencies, and broad refactors:

1. Add raw trace read/list APIs and fact support read APIs.
2. Add episode time-window retrieval.
3. Add summary retrieval behind tests now that summary writes and consolidation summaries exist.
4. Add provenance traversal across raw traces, episodes, facts, and summaries.
5. Add richer episode time/topic retrieval.
6. Add retrieval use of consolidation decay/downranking metadata after summary retrieval exists.

## Current Risk

The main project risk is assuming the documented architecture is already implemented. The current code is a useful starter memory core, but most lifecycle, provenance, conflict, consolidation, and embodied cognition behavior remains design-only.
