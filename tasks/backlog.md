# Backlog

Last audited: 2026-06-13

This backlog tracks implementation status against the V1 memory prototype. Checked items are implemented and have at least basic verification. Unchecked items may be documented, drafted in schema/interfaces, or planned, but should not be treated as complete.

## Audit and documentation

- [x] Create repository status audit in `docs/architecture/REPO_STATUS.md`
- [x] Create implementation roadmap in `docs/architecture/ROADMAP.md`
- [x] Create durable repo-audit investigation memory entry
- [x] Update `memory/MEMORY_INDEX.md`

## Foundation

- [x] Verify project structure
- [x] Run `python scripts/init_db.py`
- [x] Run `python scripts/smoke_test_memory.py`
- [x] Add pytest baseline
- [x] Add local artifact ignore rules
- [x] Add canonical development runbook
- [x] Add repeatable developer check command
- [x] Add Python 3.11 GitHub Actions CI
- [x] Add migration/table contract tests

## Memory API and CLI

- [x] Add high-level `MnemeMemory` / `MemoryEngine` facade
- [x] Wrap migration initialization, candidate scoring, raw trace storage, episode encoding, fact upsert, retrieval, consolidation, and database inspection
- [x] Add argparse CLI with `init-db`, `remember-candidate`, `add-episode`, `add-fact`, `retrieve`, `consolidate-once`, and `inspect-db`
- [x] Support JSON input/output for Codex, replay, and debug use
- [x] Add integration tests for candidate -> score -> episode/fact -> retrieve -> consolidate flow
- [x] Add memory CLI runbook
- [x] Add package console-script entry point after CLI command shape settles
- [ ] Add optional raw trace inspection commands after raw trace read/list APIs exist

## Memory models

- [x] Implement/extend `MemoryCandidate`
- [x] Implement/extend `Episode`
- [x] Implement/extend `Fact`
- [x] Implement/extend `MemoryQuery`
- [x] Implement/extend `MemoryBundle`
- [x] Add model validation for malformed confidence/salience inputs
- [x] Add timestamp, source type, status, and summary validation
- [x] Add JSON-friendly model serialization helpers
- [x] Add memory model boundary documentation
- [x] Add bounded sensory echo and working memory runtime components
- [x] Add working context snapshot export and persistence path

## Salience

- [x] Add weighted scoring
- [x] Add explicit remember override
- [x] Add promotion thresholds
- [x] Add score explanation output
- [x] Load salience weights and thresholds from `config/memory.yaml`
- [x] Add configurable promotion thresholds
- [x] Add detailed salience explanation payload
- [x] Add tests for all promotion threshold boundaries
- [x] Add salience scoring documentation

## Storage

- [x] Add migration runner
- [x] Add migration tracking table
- [x] Add raw trace writes
- [x] Add episode writes
- [x] Add fact upserts
- [x] Add fact support link writes
- [x] Add episode read-by-id API
- [x] Add fact read-by-id API
- [x] Add fact tag persistence
- [x] Add raw trace read/list APIs
- [x] Add episode time-window APIs
- [x] Add fact support read APIs
- [x] Persist episode object entities
- [x] Add working context snapshot writes/reads
- [x] Add meta-memory writes
- [x] Add meta-memory reads/updates
- [x] Add meta-memory writes during raw trace, episode, fact, and summary storage
- [x] Add memory summary writes

## Retrieval

- [x] Retrieve facts by free-text query
- [x] Retrieve facts by structured subject/predicate/object query
- [x] Retrieve facts by source type and status filters
- [x] Retrieve episodes by text query
- [x] Retrieve episodes by id/time window
- [ ] Retrieve episodes by topic
- [x] Use `MemoryQuery.entities` for retrieval ranking
- [x] Use `MemoryQuery.tags` for fact retrieval
- [x] Retrieve summaries when `include_summaries` is enabled
- [x] Rank user-confirmed facts ahead of inferred facts when relevance is similar
- [x] Exclude non-active facts from ordinary retrieval
- [x] Add deterministic retrieval reranking
- [x] Return retrieval ranking explanations
- [x] Return provenance summary
- [x] Return provenance summary derived from stored support links
- [x] Add retrieval warnings for explicitly requested non-active fact results
- [x] Update meta-memory retrieval counters for returned memories
- [x] Filter `never_say` and `internal_only` memories from ordinary retrieval

## Provenance and truth handling

- [x] Preserve source type and confidence on core models
- [x] Store source type and confidence for raw traces and facts
- [x] Store fact-to-episode support links
- [x] Normalize provenance JSON with source, derivation path, supporting memory IDs, and notes
- [x] Add speakability values: `normal`, `restricted`, `never_say`, `internal_only`
- [ ] Preserve episode `provenance_refs` as first-class stored data
- [x] Traverse raw trace -> episode -> fact support provenance
- [x] Implement user-confirmed fact precedence over inferred facts
- [x] Mark conflicting facts instead of silently overwriting

## Consolidation

- [x] Add conservative non-mutating consolidation report placeholder
- [x] Add simple summary creation
- [x] Add repeated-event clustering placeholder
- [ ] Add background consolidation conflict detection
- [x] Add decay/downranking fields
- [x] Add consolidation report tests

## Interfaces and future integration

- [x] Add Stage 3 `MnemeRuntime` one-process wiring loop
- [x] Add fake peripheral discovery for camera, microphone, and speaker inventory
- [x] Add real OS-backed camera, microphone, and speaker inventory backend
- [x] Add `mneme run --device-backend real`
- [x] Add live camera capture worker
- [x] Add live microphone transcript worker with local command adapter
- [x] Add perception-scale raw frame/transcript retention controls
- [x] Add optional built-in native camera backend after dependency choice
- [x] Add optional built-in face/person detector after model choice
- [x] Add optional built-in VAD/ASR backend after dependency choice
- [x] Add terminal virtual head command `mneme run`
- [x] Make interactive `mneme run` print responses immediately
- [x] Add explicit `mneme run --live` ticking mode for configured live perception workers
- [x] Add scripted JSON mode for deterministic virtual-head demos
- [x] Add virtual conversational presence coordinator
- [x] Add simulated speech output backend
- [x] Add optional local TTS command adapter for speech output
- [x] Add optional native local TTS backend
- [x] Persist speech voice selection as procedural memory
- [x] Add virtual avatar state for listening, thinking, speaking, idle, gaze, and safety
- [x] Add virtual skill runner with accepted/running/completed/failed/preempted/canceled statuses
- [x] Add deterministic barge-in preemption for active virtual speech
- [x] Add local model registry and `mneme models` CLI
- [x] Add Stage 6 runtime profiles for local-speech, local-vision, and local-lab
- [x] Add stdlib local browser UI command `mneme ui`
- [x] Add clean minimal local UI state surface
- [x] Add UI camera/microphone/speaker selection
- [x] Persist selected local devices for future UI and terminal runs
- [x] Add UI device inventory refresh when dropdowns only show Auto
- [x] Ground deterministic dialogue fallbacks in memory/current turn context
- [x] Add local evaluation JSONL logger and `mneme eval summarize`
- [x] Add live-speech diagnostics for ASR/no-speech/errors, duplicate suppression, TTS status, barge-in, latency, and stuck states
- [x] Add fake-backed `mneme eval speech` soak fixtures for speech hardening
- [x] Extend evaluation logs with speech-loop counters and latency fields
- [ ] Validate local-speech with real microphone, ASR model files, TTS playback, and barge-in on the current Mac
- [ ] Validate local-vision with real camera permission, OpenCV frame capture, and MediaPipe face/person observations
- [ ] Improve local browser UI from dashboard to expressive virtual head
- [x] Add local model-backed response realization behind the dialogue planner contract
- [x] Add local model runtime adapter protocol and fake adapter tests
- [x] Add Ollama/local HTTP model adapter behind optional configuration
- [x] Add `mneme cognition check` for local model availability and latency
- [x] Wire checked local model readiness into UI/runtime status displays
- [x] Add cognitive context builder from working memory, attention, safety, and retrieval
- [x] Add model dialogue realizer with deterministic fallback and schema validation
- [x] Add deterministic turn understanding before dialogue planning
- [x] Add memory review and "why did you say that?" explanation path
- [x] Add non-mutating correction/forget review proposals
- [x] Add durable memory review records for correction, forget, confirmation, and contradiction proposals
- [x] Add explicit `mneme review` list/show/apply/reject/conflicts/explain commands
- [x] Add supervised correction approval, forget suppression, confirmation upgrade, and contradiction report tests
- [x] Add cognitive benchmark fixture format and capability ladder scoring
- [x] Expand bundled cognition benchmarks for delayed recall, hallucination guard, correction approval, forget suppression, contradiction review, and self/status questions
- [x] Add UI cognitive level evidence after benchmark harness exists
- [x] Add UI memory review status and Apply/Reject controls
- [ ] Add redacted daily-driver logs and soak replay fixtures
- [ ] Add richer evaluation metrics for latency, correction rate, contradiction rate, and stuck states
- [x] Add ROS-style interface drafts
- [x] Add local runtime event model for ROS-like architecture boundaries
- [x] Add deterministic in-process event bus for tests and demos
- [x] Integrate sensory echo and working memory with local runtime events
- [x] Add deterministic simulated perception workers and scenario replay
- [x] Add deterministic Attention Manager v0 that publishes attention state
- [x] Add attention dwell/lock and target expiry behavior
- [x] Add attention priority explanations for ranked targets
- [x] Add deterministic Executive v0 that publishes intent only
- [x] Add Executive v0 priority/preemption and degraded-mode tests
- [x] Add scenario replay runbook and fixture format
- [x] Document local runtime boundaries
- [ ] Align Python models with interface drafts
- [ ] Add JSON serialization helpers for future wrappers
- [ ] Add adapters between local runtime events and interface drafts
- [x] Add virtual skill-level gaze consumer for attention state
- [x] Add virtual skill dispatcher that consumes executive intents through explicit skill interfaces
- [ ] Document future ROS node boundaries in implementation-facing docs
- [ ] Keep hardware and actuator control out of V1 memory prototype

## Documentation

- [x] Add V1 memory-first ADR
- [x] Add current repository status document
- [x] Add current roadmap document
- [x] Add local runtime architecture document
- [x] Add Attention Manager v0 documentation
- [x] Add Executive v0 documentation
- [x] Add local development runbook
- [x] Add memory CLI runbook
- [x] Add scenario replay runbook
- [x] Add Stage 3 virtual head runbook
- [x] Add Stage 5 conversational presence runbook
- [x] Add Stage 6 Local Living Lab runbook
- [x] Add local model hygiene runbook
- [x] Add cognitive capability roadmap with local model milestones and animal-reference ladder
- [x] Add sensory echo and working memory documentation
- [x] Add memory storage documentation
- [x] Add salience scoring documentation
- [x] Add memory retrieval documentation
- [x] Add provenance and meta-memory documentation
- [ ] Keep `docs/DESIGN_DOCUMENT.md` current as implementation changes
- [ ] Add ADRs for major architecture changes
