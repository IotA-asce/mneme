# Repository Status

Date: 2026-06-11
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

Implemented memory code:

- Dataclass models for `MemoryCandidate`, `SalienceFeatures`, `SalienceResult`, `Episode`, `Fact`, `MemoryQuery`, and `MemoryBundle`.
- Source and status enums for source provenance and memory lifecycle state.
- Weighted salience scoring using the documented default weights.
- Feature normalization to clamp salience inputs into `0.0..1.0`.
- Promotion decisions for echo-only, working-memory candidate, episode, and episode-plus-semantic-candidate.
- Explicit remember override when `explicit_remember_flag >= 0.9`.
- SQLite connection management and migration application through `MemoryStore`.
- Writes for raw traces, episodes, and facts.
- Fact support link writes through `fact_support`.
- Basic free-text fact search over subject, predicate, and JSON object value.
- Basic free-text episode search over summary and JSON context.
- Basic `retrieve_memory()` bundle creation over facts and episodes.
- Include flags for suppressing fact or episode retrieval.
- A conservative `consolidate_once()` placeholder that counts active episodes and performs no mutations.
- `open_default_store()` helper pointing at `.local/android_brain_memory.sqlite3`.

## Partially Implemented

The following areas exist but are not complete enough to count as full phase completion:

- Sensory echo: `raw_trace` exists and can be written, but there is no read-by-id/list API, no retention policy, and no promotion pipeline that starts from raw traces.
- Working memory: `working_context_snapshot` exists in the schema, but no model or store API writes or reads it.
- Episodic memory: episodes can be written and found by text, and participant entities are written. There is no read-by-id, time-window query, topic-specific query API, object entity persistence, or dedicated episode debug output.
- Provenance: source type, confidence, fact support links, and caller-provided trace references exist in pieces. There is no end-to-end provenance traversal, derivation chain, version history, or persisted episode provenance list.
- Semantic facts: facts can be upserted, source typed, and linked to supporting episodes. There is no conflict detection, supersession flow, source precedence, or user-confirmed outranking behavior.
- Retrieval manager: retrieval returns facts and episodes from simple text searches. It does not search working memory, summaries, or self model; does not apply the documented reranking formula; does not use query entities/tags; and does not update retrieval history.
- Consolidation: a report type and no-op pass exist. No summaries, clustering, fact extraction, conflict detection, decay, or downranking are implemented.
- Meta-memory: the `meta_memory` table exists, but no runtime code writes or reads it.
- Config: `config/memory.yaml` records defaults, but the Python code currently uses hardcoded salience weights and thresholds.

## Documented But Not Implemented

The design documents describe these future capabilities, but the repository does not yet implement them:

- Parallel perception workers for vision, speech, sound direction, touch, body state, or internal health.
- Shared world model, attention manager, executive arbiter, skill controllers, actuator bridge, and safety supervisor.
- Physical actuator control or dry-run hardware backend.
- Full ROS 2 package/runtime integration.
- Long-running memory daemon or background process.
- Promotion pipeline from observation to buffer to scoring to storage.
- Working memory lifecycle and active context management.
- Procedural memory, self model, and meta-memory behavior.
- Memory summaries and semanticization of repeated episodes.
- Forgetting, suppression, accessibility decay, detail decay, purge policy, and speakability policy.
- Contradiction review or supersession workflow.
- Structured observability logs for promotion decisions, retrieval rankings, consolidation changes, conflicts, and pruning.
- Full JSON-friendly serialization contract for future ROS wrappers.

## Current Tests

The test suite currently contains four tests:

- `tests/test_salience.py::test_explicit_remember_promotes_to_semantic_candidate`
- `tests/test_salience.py::test_low_salience_echo_only`
- `tests/test_storage_retrieval.py::test_store_trace_episode_and_fact_then_retrieve_bundle`
- `tests/test_storage_retrieval.py::test_retrieve_memory_respects_fact_and_episode_include_flags`

Coverage is focused on salience decisions, raw trace/episode/fact writes, basic retrieval, and retrieval include flags. There are no tests yet for migrations as a standalone contract, malformed inputs, fact conflict behavior, provenance traversal, retrieval reranking, consolidation mutations, decay/downranking, or working context snapshots.

## Verification Commands

Recommended clean local verification:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
```

When the package is not installed but dependencies are already present, scripts can also be run with:

```bash
PYTHONPATH=src python3 scripts/init_db.py
PYTHONPATH=src python3 scripts/smoke_test_memory.py
PYTHONPATH=src python3 -m pytest
```

There is no configured lint, typecheck, formatter, or build command beyond package installation and tests.

## Safest Next Tasks

The safest next tasks should stay inside the memory prototype and avoid hardware, ROS runtime, new dependencies, and broad refactors:

1. Add storage contract tests for the migration tables, raw trace reads, episode participant persistence, and fact support links.
2. Add small read APIs for raw traces, episodes, and fact support links before expanding retrieval behavior.
3. Implement structured fact retrieval by subject/predicate/topic with tests.
4. Add meta-memory writes for stored facts and episodes, preserving source type and provenance.
5. Add retrieval reranking behind tests using only existing SQLite data and dataclasses.
6. Turn `consolidate_once()` into a minimal summary-producing pass only after storage and retrieval contracts are stronger.

## Current Risk

The main project risk is assuming the documented architecture is already implemented. The current code is a useful starter memory core, but most lifecycle, provenance, conflict, consolidation, and embodied cognition behavior remains design-only.
