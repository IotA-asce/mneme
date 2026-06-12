# Backlog

Last audited: 2026-06-12

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
- [ ] Add package console-script entry point after CLI command shape settles
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
- [ ] Add raw trace read/list APIs
- [ ] Add episode time-window APIs
- [ ] Add fact support read APIs
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
- [ ] Retrieve episodes by id/time/topic
- [x] Use `MemoryQuery.entities` for retrieval ranking
- [x] Use `MemoryQuery.tags` for fact retrieval
- [ ] Retrieve summaries when `include_summaries` is enabled
- [x] Rank user-confirmed facts ahead of inferred facts when relevance is similar
- [x] Exclude non-active facts from ordinary retrieval
- [x] Add deterministic retrieval reranking
- [x] Return retrieval ranking explanations
- [x] Return provenance summary
- [ ] Return provenance summary derived from stored support links
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
- [ ] Traverse raw trace -> episode -> fact support provenance
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
- [ ] Add skill-level gaze consumer for attention state
- [ ] Add skill dispatcher that consumes executive intents through explicit skill interfaces
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
- [x] Add sensory echo and working memory documentation
- [x] Add memory storage documentation
- [x] Add salience scoring documentation
- [x] Add memory retrieval documentation
- [x] Add provenance and meta-memory documentation
- [ ] Keep `docs/DESIGN_DOCUMENT.md` current as implementation changes
- [ ] Add ADRs for major architecture changes
