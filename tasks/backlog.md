# Backlog

Last audited: 2026-06-11

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
- [ ] Add working context model

## Salience

- [x] Add weighted scoring
- [x] Add explicit remember override
- [x] Add promotion thresholds
- [x] Add score explanation output
- [ ] Load salience weights and thresholds from `config/memory.yaml`
- [ ] Add tests for all promotion threshold boundaries

## Storage

- [x] Add migration runner
- [x] Add migration tracking table
- [x] Add raw trace writes
- [x] Add episode writes
- [x] Add fact upserts
- [x] Add fact support link writes
- [x] Add episode read-by-id API
- [x] Add fact read-by-id API
- [ ] Add raw trace read/list APIs
- [ ] Add episode time-window APIs
- [ ] Add fact support read APIs
- [x] Persist episode object entities
- [x] Add working context snapshot writes/reads
- [x] Add meta-memory writes
- [x] Add meta-memory reads/updates

## Retrieval

- [x] Retrieve facts by free-text query
- [ ] Retrieve facts by structured subject/predicate/topic query
- [x] Retrieve episodes by text query
- [ ] Retrieve episodes by id/time/topic
- [ ] Use `MemoryQuery.entities`
- [ ] Use `MemoryQuery.tags`
- [ ] Retrieve summaries when `include_summaries` is enabled
- [ ] Add reranking
- [x] Return provenance summary
- [ ] Return provenance summary derived from stored support links
- [ ] Add retrieval warnings for conflicting or suppressed results

## Provenance and truth handling

- [x] Preserve source type and confidence on core models
- [x] Store source type and confidence for raw traces and facts
- [x] Store fact-to-episode support links
- [ ] Preserve episode `provenance_refs` as first-class stored data
- [ ] Traverse raw trace -> episode -> fact support provenance
- [ ] Implement user-confirmed fact precedence over inferred facts
- [ ] Mark conflicting facts instead of silently overwriting

## Consolidation

- [x] Add conservative non-mutating consolidation report placeholder
- [ ] Add simple summary creation
- [ ] Add repeated-event clustering placeholder
- [ ] Add conflict detection
- [ ] Add decay/downranking fields
- [ ] Add consolidation report tests

## Interfaces and future integration

- [x] Add ROS-style interface drafts
- [ ] Align Python models with interface drafts
- [ ] Add JSON serialization helpers for future wrappers
- [ ] Document future ROS node boundaries in implementation-facing docs
- [ ] Keep hardware and actuator control out of V1 memory prototype

## Documentation

- [x] Add V1 memory-first ADR
- [x] Add current repository status document
- [x] Add current roadmap document
- [x] Add local development runbook
- [x] Add memory storage documentation
- [ ] Keep `docs/DESIGN_DOCUMENT.md` current as implementation changes
- [ ] Add ADRs for major architecture changes
