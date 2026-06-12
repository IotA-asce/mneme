# Implementation Plan

## Phase 1 — Extraction Core

- `extraction.py`:
  - `statement_fact_id(subject, predicate, value)` — deterministic `fact_<sha256[:12]>` over canonical JSON.
  - `FactExtractionReport` dataclass (episode_id, statements_found, facts_upserted, conflicts_flagged, fact_ids, skipped reasons) with `to_dict()`.
  - `FactExtractor(engine, *, bus=None, source="fact_extractor", confidence_cap=0.75, clock=None)`:
    - `extract_from_episode(episode_or_id)` parsing `context["statements"]`, validating each statement, building `model_inferred` facts supported by the episode, upserting through `engine.add_fact` with derivation path `["episode", "extraction", "fact"]`,
    - confidence = `min(episode.confidence, statement confidence if given, confidence_cap)`,
    - `attach_to_bus(bus)` subscribing to `memory_lifecycle` events; promotion events with `semantic_candidate=true` and an `episode_id` trigger extraction,
    - extraction results published as `memory_lifecycle` events (`lifecycle_stage="extraction"`),
    - `extract_recent(limit)` batch helper over recent episodes.

## Phase 2 — Tests (written first)

- `tests/test_fact_extraction.py`: statement extraction with provenance, confidence capping, idempotent re-extraction, malformed statement skipping, conflict precedence versus user-confirmed facts, bus-driven end-to-end (candidate event → promotion → extraction → fact) including lifecycle event assertions.

## Phase 3 — Docs and Status

- `docs/memory/EXTRACTION.md` (new), `MASTER_ROADMAP.md` M1.2, `REPO_STATUS.md`, memory entry + index.

## Validation

- `python -m pytest tests/test_fact_extraction.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Extraction core → bus integration → tests green → docs.

## Rollback

Revert `extraction.py`, tests, docs. No schema changes.

## Definition of Done

- Replay of a scenario with structured statements yields facts with provenance chains episode→trace, automatically, idempotently.
- Conflicts with user-confirmed facts are flagged, never overwritten.
- Full suite passes.
