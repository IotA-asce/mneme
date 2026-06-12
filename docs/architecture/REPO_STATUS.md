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
- ROS-style interface drafts under `interfaces/`, aligned field-for-field with the Python domain models and enforced by `tests/test_interface_alignment.py`; these are documentation/contract drafts, not generated runtime bindings.
- A documented JSON serialization contract (`docs/architecture/SERIALIZATION.md`) and a phased ROS integration plan with node boundary notes (`docs/architecture/ROS_INTEGRATION_PLAN.md`).
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
- Raw trace lookup by ID and recent raw trace listing with source-type filtering.
- Direct fact support link reads in both directions (`get_fact_support`, `get_facts_for_episode`).
- Episode retrieval by overlapping time window.
- Read-only provenance chain traversal (`get_provenance_chain`) over raw traces, episodes, facts, and summaries with missing-reference reporting.
- Free-text and structured fact search over subject, predicate, object text, source type, status, and tags.
- Basic free-text episode search over summary and JSON context.
- `retrieve_memory()` bundle creation over facts, episodes, and memory summaries.
- Retrieval warnings for empty results, speakability-withheld candidates, explicit non-active status filters, and conflicting fact groups.
- Bundle provenance summaries derived from stored provenance chains for returned items.
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
- Automatic memory promotion (`MemoryPromoter`): bus-driven candidate scoring and storage per salience decision, with `memory_lifecycle` observability events.
- Deterministic fact extraction (`FactExtractor`): structured episode statements become conflict-aware `model_inferred` facts automatically after semantic-candidate promotions.
- Schedulable consolidation daemon (`ConsolidationDaemon`): interval-policed, batch-bounded consolidation passes with lifecycle events and cumulative stats, driven by injected-clock ticks (no threads).
- Staged forgetting (`decay.py`): retrieval-time downranking from decay metadata, deterministic suppression passes for summarized episodes and superseded facts, and explicit provenance-preserving purge tombstones with user-confirmed protection.
- Full lifecycle observability: `memory_lifecycle` events for promotion, extraction, consolidation, decay, retrieval, and fact conflicts (engine `event_bus` opt-in; content never leaks into events), plus `inspect-provenance` / `inspect-decay` CLI commands.
- Shared world model (`WorldModel`): typed TTL-bounded fusion of perception events (persons, active speaker, sound, touch, internal state, safety level) publishing `world_state_update` events with deterministic snapshots.
- Interaction-bounded context windows (`ContextWindowManager`): open on speech/person/touch, close on idle timeout or explicit boundary, persisting working-memory snapshots automatically.
- Attention v1: habituation, inhibition-of-return, opt-in idle curiosity scanning, and bounded state history on top of the v0 weighted target ranking.
- Executive v1: goal stack with safety suspension/resumption, opt-in response timing, memory-informed intents with conflict-driven clarification flags, and deterministic idle behavior rotation.
- Dialogue planner v0: deterministic act selection (answer/clarify/acknowledge/greet or safety silence) producing structured, speakability-filtered utterance plans from executive intent and memory bundles.
- Self model v0 and procedural memory v0: reserved-subject identity facts with deliberate in-place updates, and versioned skill parameters with supersession chains and provenance notes.
- Stage 3 runtime and virtual head: `MnemeRuntime` wires the local event bus, memory engine, world model, sensory echo, working memory, context windows, attention, executive, dialogue planner, promotion, extraction, consolidation daemon, and fake peripheral discovery into one deterministic process.
- Terminal virtual head command: `mneme run` accepts typed input, publishes `speech_transcript` perception events, renders dialogue plans as text, and supports scripted JSON output for deterministic demos.
- Fake peripheral discovery: deterministic camera/microphone/speaker inventory publication with tests for device appearance, removal, and absence.

## Partially Implemented

The following areas exist but are not complete enough to count as full phase completion:

- Sensory echo: `raw_trace` rows can be written, read by ID, and listed newest-first with a source-type filter. There is still no retention policy and no promotion pipeline that starts from raw traces.
- Working memory: `WorkingMemory` maintains a bounded active context with automatic interaction-bounded context windows (`ContextWindowManager`) that persist snapshots at close boundaries. There is no long-running working-memory daemon yet.
- Episodic memory: episodes can be written, found by text, retrieved by ID, and queried by overlapping time window. Participant and object entities are persisted through `episode_entity`. There is no topic-specific query API, first-class persisted episode provenance list, or dedicated episode debug output.
- Provenance: source type, confidence, fact support links, normalized meta-memory provenance JSON, retrieval counters, and speakability are stored, and `get_provenance_chain()` traverses fact → episode → raw trace derivations end-to-end with missing-reference reporting. There is still no version history or persisted episode provenance list.
- Semantic facts: facts can be upserted, source typed, tagged, searched by structured fields, linked to supporting episodes, checked for conservative semantic conflicts, marked `superseded`/`conflicted`, and queried through conflict reports.
- Retrieval manager: retrieval returns reranked facts, episodes, and memory summaries from local SQLite, updates meta-memory retrieval history for returned records, filters internal-only speakability records by default, warns about empty/withheld/conflicting results, and derives the bundle provenance summary from stored support links. It does not search working memory or self model.
- Consolidation: a one-shot deterministic pass can create repeated-episode summaries and meta-memory decay hints. No long-running daemon, fact extraction, contradiction review, purge behavior, or retrieval downranking is implemented.
- Meta-memory: typed storage methods exist for records, provenance JSON, speakability, and retrieval history updates.
- Config: `config/memory.yaml` records salience defaults that can be loaded when requested.

## Documented But Not Implemented

The design documents describe these future capabilities, but the repository does not yet implement them:

- Real perception workers for vision, speech, sound direction, touch, body state, or internal health.
- Skill controllers, actuator bridge, and safety supervisor (the shared world model, attention manager v0, and executive arbiter v0 are implemented).
- Physical actuator control or dry-run hardware backend.
- Full ROS 2 package/runtime integration.
- Real platform camera/microphone/speaker discovery backends.
- Spoken TTS and visual avatar rendering.
- Long-running memory daemon or background process.
- Procedural learning behavior (self model and procedural parameter storage are implemented; autonomous learning is deferred).
- Semanticization of consolidation summaries into facts (structured episode statements are implemented).
- Detail decay (in-place content summarization) and raw trace retention policy (accessibility decay, suppression, and explicit purge are implemented).
- Contradiction review or supersession workflow.

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
- `tests/test_stage3_runtime.py::test_runtime_starts_with_fake_peripherals_and_publishes_inventory`
- `tests/test_stage3_runtime.py::test_typed_virtual_head_remembers_and_answers_from_memory`
- `tests/test_stage3_runtime.py::test_scenario_fixture_runs_through_runtime_stack`

Coverage is focused on model validation, salience decisions, raw trace/episode/fact/summary writes, migration tracking, meta-memory storage, provenance normalization, speakability filtering, retrieval history updates, working context snapshots, structured fact retrieval, deterministic retrieval reranking, semantic fact conflict handling, basic episode retrieval, repeated-episode consolidation summaries, consolidation decay metadata, retrieval include flags, the high-level memory API/CLI conversation-like flow, local runtime event publication/subscription behavior, bounded sensory echo/working-memory behavior, deterministic scenario replay, fake peripheral discovery, and the Stage 3 typed virtual-head runtime. There are no tests yet for real OS peripheral discovery, real sensor workers, spoken output, visual avatar rendering, skill controllers, actuator bridges, ROS adapters, or cross-process runtime behavior.

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
