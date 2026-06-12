# Core Idea: Deterministic Fact Extraction (Stage 1 / M1.2)

## Problem Statement

Episodes are stored but never semanticized: the `semanticize` step of the memory lifecycle is missing. The promoter (M1.1) flags `episode_and_semantic_candidate` outcomes, but nothing turns those episodes into semantic facts, so knowledge never accumulates in the fact store automatically.

## Desired Outcome

- A deterministic `FactExtractor` that extracts entity–predicate–value facts from structured episode context (`context["statements"]`), entering them through the existing conflict-aware `add_fact` path as `model_inferred` — never as confirmed.
- Event-driven operation: the extractor subscribes to `memory_lifecycle` promotion events and extracts from flagged semantic candidates automatically.
- Deterministic fact IDs derived from statement content so re-extraction is idempotent (no duplicates).
- Extraction results published as `memory_lifecycle` events (`lifecycle_stage="extraction"`).

## User / Project Value

Completes `observe → … → promote → semanticize` for explicitly-structured knowledge: a replayed "remember that I prefer X" scenario now produces a queryable fact with full provenance to its episode and raw trace — automatically.

## Affected Systems

- `src/android_brain_memory/extraction.py` (new), `__init__.py` exports
- `tests/test_fact_extraction.py` (new)
- `docs/memory/EXTRACTION.md` (new), roadmap/status docs

## Assumptions

- V1 extraction is *structured-context-first* per the master roadmap: statements arrive as `context["statements"]` entries (`{subject, predicate, value, confidence?}`), typically authored in scenario candidate payloads or by future perception/dialogue workers. Free-text NLP extraction is explicitly out of scope (and LLM extraction is deferred to Stage 7).
- Conflict precedence is already correct in storage: an extracted inferred fact that contradicts a user-confirmed fact becomes `conflicted` while the confirmed fact stays active.

## Constraints

- Deterministic, standard library only, no schema changes.
- Extracted facts are always `model_inferred` with confidence capped (default 0.75) — inference must never masquerade as confirmation.
- Malformed statements are skipped with recorded reasons, never raised out of bus callbacks.

## Non-Goals

- Free-text or LLM-based extraction.
- Extraction from consolidation summaries (a future increment once summary semantics stabilize).
- Conflict resolution workflows (Stage 7 / M7.4).

## Risks

- Garbage-in statements produce garbage facts; mitigated by validation, the confidence cap, `model_inferred` labeling, and full provenance.
- Deterministic IDs mean a re-stated fact updates rather than versions; acceptable for V1 and recorded as a known behavior.
