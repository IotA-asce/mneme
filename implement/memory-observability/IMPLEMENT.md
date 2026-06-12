# Implementation Plan

## Phase 1 — Engine Eventing

- `MnemeMemory.__init__` gains `event_bus=None`, `event_source="memory_engine"`, `clock=None` (ms).
- `retrieve()` publishes `lifecycle_stage="retrieval"` events: query_id, query_text, requester, query_type, fact/episode/summary IDs, warnings.
- `add_fact()` publishes `lifecycle_stage="conflict"` events with the JSON-able conflict report when one is produced.

## Phase 2 — Storage Read

- `get_meta_memory_with_decay(limit=50)`: meta-memory rows whose provenance carries a `decay` mapping, deterministic order.

## Phase 3 — CLI

- `inspect-provenance --memory-id <id> --memory-kind <kind>` → provenance chain JSON.
- `inspect-decay [--limit N]` → decay-bearing meta-memory records.

## Phase 4 — Tests (written first)

- `tests/test_observability.py`: retrieval event payload (IDs + warnings, no content), conflict event on conflicting upsert, no events without a bus, storage decay listing, CLI inspect-provenance and inspect-decay output.

## Phase 5 — Docs and Status

- `docs/runbooks/MEMORY_CLI.md` new commands; `docs/memory/PROVENANCE.md` observability note; `MASTER_ROADMAP.md` M1.5 + Stage 1 gate; `REPO_STATUS.md`; memory entry + index.

## Validation

- `python -m pytest tests/test_observability.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Storage read → engine eventing → CLI → docs.

## Rollback

Revert engine/storage/cli/test/doc changes. No schema changes; `event_bus` is opt-in so omitting it restores prior behavior exactly.

## Definition of Done

- Promotion, extraction, consolidation, decay, retrieval, and conflict are all observable as `memory_lifecycle` events.
- Provenance chains and decay state inspectable from the CLI.
- Full suite passes.
