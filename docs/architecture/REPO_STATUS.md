# Repository Status

Date: 2026-06-13
Status: Current repository capability audit

This audit records what the repository actually implements today versus what the design documents describe for the broader Mneme architecture.

## Current Implementation

The repository currently implements a local Python virtual-head prototype with deterministic memory, cognition, live-perception adapter contracts, virtual conversational presence, and the Stage 6 Local Living Lab foundation. It does not control physical hardware, run ROS 2 nodes, use a vector database, call cloud LLM services, run a local LLM dialogue model, or bundle local model files as required assets.

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
- Dialogue planner v0: deterministic act selection (answer/clarify/acknowledge/greet or safety silence) producing structured, speakability-filtered utterance plans from executive intent, facts, episodes, and current-turn context.
- Self model v0 and procedural memory v0: reserved-subject identity facts with deliberate in-place updates, and versioned skill parameters with supersession chains and provenance notes.
- Stage 3 runtime and virtual head: `MnemeRuntime` wires the local event bus, memory engine, world model, sensory echo, working memory, context windows, attention, executive, dialogue planner, promotion, extraction, consolidation daemon, and fake peripheral discovery into one deterministic process.
- Terminal virtual head command: `mneme run` accepts typed input, publishes `speech_transcript` perception events, renders dialogue plans as text, and supports scripted JSON output for deterministic demos.
- Fake peripheral discovery: deterministic camera/microphone/speaker inventory publication with tests for device appearance, removal, and absence.
- Real device discovery inventory: `RealPeripheralBackend` can list host cameras, microphones, and speakers through best-effort OS inventory commands, exposed by `mneme run --device-backend real`. It does not open sensors or verify capture permissions.
- Stage 4 live perception: `LiveVisionWorker` and `LiveSpeechWorker` select discovered devices, run configured local command adapters, publish standard perception events, store raw frame/transcript traces, create memory candidates, and enforce bounded frame archive retention.
- Perception fusion and calibration: `PerceptionFusionCalibrator` publishes speaker/person match diagnostics with latency and confidence as world-state updates.
- Stage 5 conversational presence: dialogue plans become virtual speech skill goals; simulated speech output is recorded in JSON; optional local TTS command adapters can play speech through host tools; selected speech voice labels persist as procedural memory; `VirtualAvatarController` exposes listening/thinking/speaking/idle/safety avatar state; `VirtualSkillRunner` publishes accepted/running/completed/failed/preempted/canceled status events; barge-in preempts active virtual speech on user speech.
- Stage 6 optional local backends: `SoundDeviceMicrophoneRecorder`, `WebRtcVadEndpointDetector`, `FasterWhisperSpeechRecognitionBackend`, `KokoroSpeechOutputBackend`, `OpenCVCameraCaptureBackend`, and `MediaPipeFaceDetectionBackend` sit behind the existing speech/vision/output contracts and are dependency-isolated behind optional extras.
- Stage 6 model hygiene: `config/models.yaml` describes local model IDs, backend, path, license/source notes, checksum if known, and enabled profiles. `mneme models list`, `mneme models verify`, and guarded `mneme models download` inspect those records. Model files belong under `.local/models/` and are ignored by git.
- Stage 6 local cognition: `model_runtime.py` provides a fake model runtime and a stdlib HTTP Ollama adapter. `mneme cognition check` verifies the Ollama service, installed model list, and optional bounded non-streaming `/api/chat` probe for the default `qwen2.5:1.5b` model.
- Local model-backed wording: `cognitive_context.py` builds bounded, speakability-filtered context packets from working memory, attention, safety/avatar state, retrieval results, ranking explanations, and provenance summaries. `model_dialogue.py` lets a checked local model realize final wording after deterministic dialogue planning, validates structured JSON output, rejects invented memory refs and source-status misrepresentation, hedges low-confidence memory use, and falls back to deterministic text on failure.
- Stage 6 Local Living Lab CLI: `mneme run --profile local-speech`, `mneme run --profile local-vision`, and `mneme run --profile local-lab` opt into native local backends when optional dependencies and local models are present, while command adapters, fake devices, terminal mode, and JSON mode remain supported.
- Stage 6 browser UI: `mneme ui` serves a stdlib local dashboard that reads runtime/avatar/cognition snapshots, renders state, submits typed user input, refreshes the local device inventory, saves preferred camera/microphone/speaker selections, and can show local model status without owning cognition.
- Stage 6 device preferences: `.local/runtime_preferences.json` stores selected camera, microphone, and speaker IDs. `mneme ui` saves the file; `mneme run` and `mneme ui` load it on future runs, while terminal `--camera-device-id`, `--microphone-device-id`, and `--speaker-device-id` flags can override selections for one run.
- Stage 6 evaluation logging: `EvaluationLogger`, `mneme run --evaluation-log`, and `mneme eval summarize` record JSONL daily-driver metrics for response generation, memory recall signal, skill-status count, safety-event count, and barge-in count.
- M8/M10 memory review loop: `turn_understanding.py` classifies correction, forget, confirmation, contradiction, explanation, memory-review, self, capability, and status turns before dialogue planning. `memory_review.py` now creates durable review records and explicit apply/reject flows for corrections, forget requests, confirmations, and contradiction review.
- M8 CLI/UI evidence: `mneme eval cognition --json` runs the bundled cognition suite, `mneme eval cognition --fixture ... --json` still runs one fixture, `mneme eval capability --json` reports conservative capability evidence, `mneme review ...` exposes supervised review actions, and `mneme ui` shows latest review state without owning cognition.

## Partially Implemented

The following areas exist but are not complete enough to count as full phase completion:

- Sensory echo: `raw_trace` rows can be written, read by ID, and listed newest-first with a source-type filter. There is still no retention policy and no promotion pipeline that starts from raw traces.
- Working memory: `WorkingMemory` maintains a bounded active context with automatic interaction-bounded context windows (`ContextWindowManager`) that persist snapshots at close boundaries. There is no long-running working-memory daemon yet.
- Episodic memory: episodes can be written, found by text, retrieved by ID, and queried by overlapping time window. Participant and object entities are persisted through `episode_entity`. There is no topic-specific query API, first-class persisted episode provenance list, or dedicated episode debug output.
- Provenance: source type, confidence, fact support links, normalized meta-memory provenance JSON, retrieval counters, and speakability are stored, and `get_provenance_chain()` traverses fact → episode → raw trace derivations end-to-end with missing-reference reporting. There is still no version history or persisted episode provenance list.
- Semantic facts: facts can be upserted, source typed, tagged, searched by structured fields, linked to supporting episodes, checked for conservative semantic conflicts, marked `superseded`/`conflicted`, and queried through conflict reports.
- Retrieval manager: retrieval returns reranked facts, episodes, and memory summaries from local SQLite, updates meta-memory retrieval history for returned records, filters internal-only speakability records by default, warns about empty/withheld/conflicting results, and derives the bundle provenance summary from stored support links. It does not search working memory or self model.
- Consolidation: one-shot and tick-driven daemon paths can create repeated-episode summaries, emit lifecycle events, and write meta-memory decay hints consumed by retrieval. Semanticization of consolidation summaries, contradiction review, and a supervised long-running service process remain future work.
- Meta-memory: typed storage methods exist for records, provenance JSON, speakability, and retrieval history updates.
- Config: `config/memory.yaml` records salience defaults that can be loaded when requested.
- Conversational presence: virtual speech, avatar state, virtual skill status, local TTS command integration, and a lightweight local browser UI are implemented. Polished graphical avatar rendering, speaker device routing, and physical skills remain outside the repo-owned implementation.
- Native local speech and vision: optional wrappers exist and are unit-tested with fake devices/models. Real microphone permissions, faster-whisper model placement, Kokoro compatibility, camera permissions, MediaPipe model quality, and end-to-end latency are manual/local validation tasks rather than CI-verified behavior.
- Local model management: the registry and verification CLI exist. File-managed model entries intentionally do not auto-download model files until exact sources/licenses/checksums are documented. Ollama-managed model entries are listed in the registry but verified through `mneme cognition check`.
- Cognitive capability roadmap: `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md` defines the local model integration path, animal-reference capability ladder, benchmark harness, and physical embodiment readiness gate. M7.1-M7.4 are implemented as local model readiness, context building, model wording, and runtime/UI status. M8 now has benchmark, turn-understanding, memory-review, and capability-evidence foundations; broad soak benchmarks remain future work.

## Documented But Not Implemented

The design documents describe these future capabilities, but the repository does not yet implement them:

- Bundled native model files for face detection, VAD, ASR, or TTS. Stage 6 provides optional wrappers and a model registry, but real files live outside git under `.local/models/`.
- Local LLM-backed reasoning or planning. Local model-backed wording is available, but the current planner, memory retrieval, executive intent, and safety boundaries remain deterministic.
- Polished graphical avatar rendering. Stage 6 provides a local browser dashboard; it is not an expressive avatar renderer.
- Physical skill controllers, actuator bridge, and safety supervisor (virtual skills and safety-state reactions are implemented; physical command paths are not).
- Physical actuator control or dry-run hardware backend.
- Full ROS 2 package/runtime integration.
- Long-running memory daemon or background process.
- Private-log redaction and replayable soak scenarios from real daily-driver logs.
- Bounded procedural adaptation from evaluation metrics.
- Procedural learning behavior (self model and procedural parameter storage are implemented; autonomous learning is deferred).
- Semanticization of consolidation summaries into facts (structured episode statements are implemented).
- Detail decay (in-place content summarization) and raw trace retention policy (accessibility decay, suppression, and explicit purge are implemented).
- Automated contradiction resolution workflow. Contradiction reports and supervised review records exist, but Mneme does not auto-resolve confirmed-vs-confirmed conflicts.

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
- `tests/test_conversational_presence.py::test_virtual_skill_runner_emits_speech_statuses_and_records_output`
- `tests/test_conversational_presence.py::test_runtime_speaks_dialogue_plan_and_updates_avatar`
- `tests/test_conversational_presence.py::test_runtime_persists_speech_voice_in_procedural_memory`
- `tests/test_conversational_presence.py::test_runtime_barge_in_preempts_active_speech`
- `tests/test_conversational_presence.py::test_virtual_avatar_tracks_attention_and_safety`
- `tests/test_conversational_presence.py::test_mneme_run_tts_command_json_output`
- `tests/test_stage6_local_living_lab.py::test_model_registry_verifies_existing_and_missing_models`
- `tests/test_stage6_local_living_lab.py::test_model_registry_supports_service_managed_ollama_records`
- `tests/test_model_runtime.py::test_ollama_chat_sends_non_streaming_request_and_parses_response`
- `tests/test_model_runtime.py::test_ollama_check_reports_missing_model_with_pull_suggestion`
- `tests/test_model_runtime.py::test_cognition_check_json_cli_failure_returns_nonzero`
- `tests/test_cognitive_context.py::test_cognitive_context_filters_internal_and_redacts_restricted`
- `tests/test_cognitive_context.py::test_cognitive_context_enforces_budget_deterministically`
- `tests/test_model_dialogue.py::test_model_dialogue_realizer_uses_valid_model_json`
- `tests/test_model_dialogue.py::test_model_dialogue_realizer_rejects_invented_memory_refs`
- `tests/test_model_dialogue.py::test_model_dialogue_realizer_rejects_confirmed_claim_for_inferred_fact`
- `tests/test_stage3_runtime.py::test_runtime_can_realize_dialogue_with_injected_local_model`
- `tests/test_stage3_runtime.py::test_mneme_run_local_cognition_profile_uses_model_realizer`
- `tests/test_turn_understanding.py::test_turn_classifier_covers_requested_categories`
- `tests/test_memory_review.py::test_apply_correction_review_writes_user_confirmed_fact_and_supersedes_old_fact`
- `tests/test_cognitive_benchmarks.py::test_cognitive_benchmark_suite_runs_bundled_fixtures`
- `tests/test_capability_ladder.py::test_capability_report_uses_benchmark_evidence`
- `tests/test_stage6_local_living_lab.py::test_faster_whisper_backend_uses_injected_recorder_and_model`
- `tests/test_stage6_local_living_lab.py::test_opencv_camera_backend_uses_injected_cv2_and_face_detector`
- `tests/test_stage6_local_living_lab.py::test_evaluation_logger_records_and_summarizes_turn`

Coverage is focused on model validation, salience decisions, raw trace/episode/fact/summary writes, migration tracking, meta-memory storage, provenance normalization, speakability filtering, retrieval history updates, working context snapshots, structured fact retrieval, deterministic retrieval reranking, semantic fact conflict handling, supervised memory review apply/reject flows, basic episode retrieval, repeated-episode consolidation summaries, consolidation decay metadata, retrieval include flags, the high-level memory API/CLI conversation-like flow, local runtime event publication/subscription behavior, bounded sensory echo/working-memory behavior, deterministic scenario replay, fake peripheral discovery, injected-output real peripheral discovery parsing, command-adapter live perception workers, perception fusion diagnostics, bounded frame archive retention, typed virtual-head runtime, virtual conversational presence, Stage 6 fake local audio/vision/model backends, local model CLI, local model context building, model dialogue realization/fallback validation, deterministic turn understanding, memory-backed response explanation, cognitive benchmark suite scoring, conservative capability ladder reports, browser UI rendering, and evaluation logging. There are no CI tests for real microphone/camera devices, real ASR/TTS/vision models, physical skill controllers, actuator bridges, ROS adapters, or cross-process runtime behavior.

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

The safest next tasks should stay inside the Local Living Lab and avoid physical hardware, ROS runtime, required heavyweight dependencies, and broad refactors:

1. Add live-speech interruption benchmarks and soak replay fixtures for barge-in, duplicate-response prevention, latency, and recovery.
2. Manually validate `local-cognition` with the installed `qwen2.5:1.5b` model across a few real typed sessions and record latency/fallback behavior.
3. Manually validate `local-speech` on the current Mac: microphone permissions, faster-whisper model placement, local TTS playback, barge-in, and no duplicate spoken responses.
4. Manually validate `local-vision`: camera permissions, OpenCV frame capture, MediaPipe face/person observations, and anonymous-session person continuity.
5. Add redacted daily-driver logs and soak replay fixtures from real local runs.
6. Add person-scoped continuity review after live vision/person tracking is validated.
7. Improve the local browser UI from dashboard to expressive virtual head while keeping cognition outside the UI.
8. Keep physical embodiment work deferred until explicit hardware safety planning resumes.

## Current Risk

The main project risk is assuming local-brain progress implies physical safety. The current code has a useful local virtual-head stack and Stage 6 optional local backend seams, but real media quality, model performance, polished graphical presence, long-running supervision, ROS integration, and any physical actuator behavior remain future work.
