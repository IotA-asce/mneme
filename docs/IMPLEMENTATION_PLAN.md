# Implementation Plan

## Phase 0 — Project bootstrapping

Deliverables:

- repo structure
- database migration
- Python package skeleton
- initial tests
- smoke scripts

Exit criteria:

- `python scripts/init_db.py` creates the database
- `python scripts/smoke_test_memory.py` runs without error

## Phase 1 — Salience and raw trace storage

Deliverables:

- `MemoryCandidate` model
- `SalienceFeatures` model
- salience scorer
- raw trace table write/read
- promotion decision function

Exit criteria:

- low-salience candidate is ignored/echo-only
- high-salience candidate is marked for episode storage
- explicit remember flag can override threshold

## Phase 2 — Episodic memory

Deliverables:

- episode schema writes
- provenance link support
- episode retrieval by id/time/topic
- episode debug output

Exit criteria:

- a conversation-like event can become an episode
- episode can be retrieved by keyword/topic

## Phase 3 — Semantic facts

Deliverables:

- fact model
- fact upsert
- fact support links
- user-confirmed vs inferred status
- basic conflict detection

Exit criteria:

- user-confirmed fact outranks inferred fact
- conflicting facts are marked, not silently overwritten

## Phase 4 — Retrieval manager

Deliverables:

- `MemoryQuery`
- `MemoryBundle`
- structured retrieval over facts and episodes
- reranking
- provenance summary

Exit criteria:

- query for a topic/person returns relevant facts and episodes
- response includes confidence and source types

## Phase 5 — Consolidation skeleton

Deliverables:

- consolidation pass
- clustering placeholder
- summary creation
- decay/downranking fields
- consolidation report

Exit criteria:

- repeated events can produce a summary
- low-value items are marked for decay/downranking

## Phase 6 — Prepare for ROS integration

Deliverables:

- align Python models with `interfaces/`
- event serialization format
- node boundary notes
- future launch plan

Exit criteria:

- memory core can be wrapped by future ROS nodes without changing domain models
