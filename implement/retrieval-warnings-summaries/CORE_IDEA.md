# Core Idea: Retrieval Warnings, Summary Retrieval, and Derived Provenance Summaries

## Problem Statement

Roadmap Phase 4 (retrieval ranking) left three gaps:

- `MemoryQuery.include_summaries` exists but summaries are never retrieved or ranked, so consolidation output is invisible to retrieval.
- `MemoryBundle.warnings` only reports non-active status filters; empty, speakability-withheld, and conflicting results pass silently.
- `MemoryBundle.provenance_summary` is a hardcoded sentence instead of being derived from stored support links.

## Desired Outcome

- Text queries return ranked memory summaries alongside facts and episodes, capped by `max_results`, honoring `include_summaries` and speakability policy, and updating retrieval history.
- Retrieval warns when nothing matched, when candidates were withheld by speakability policy, and when returned facts have conflicting records.
- `provenance_summary` is generated from the Phase 1 provenance chain reads for the returned items.

## User / Project Value

The executive and future dialogue planning can trust the bundle: consolidated knowledge is reachable, silent gaps become visible warnings, and every answer can explain where it came from.

## Affected Systems

- `src/android_brain_memory/models.py` (`MemoryBundle.summaries`)
- `src/android_brain_memory/storage.py` (`search_memory_summaries`)
- `src/android_brain_memory/retrieval.py` (summary candidates, warnings, provenance summary)
- `tests/`, `docs/memory/RETRIEVAL.md`, `docs/memory/PROVENANCE.md`, roadmap/status docs

## Assumptions

- Summaries written by `store_memory_summary()` carry meta-memory rows with kind `summary` so speakability filtering and retrieval counters work unchanged.
- The Phase 1 `get_provenance_chain()` API is available for provenance summary generation.

## Constraints

- Deterministic ranking and warning text; standard library only; no schema changes.
- Existing bundle consumers must keep working: `summaries` defaults to an empty list, existing fields unchanged.

## Non-Goals

- Summary-specific ranking weights (summaries reuse the existing weighted factors).
- Conflict resolution workflows; warnings only surface the condition.
- Retrieval-time decay/downranking from consolidation hints.
- Working-memory or self-model retrieval.

## Risks

- Bundles get slightly larger; mitigated by `max_results` caps and the `include_summaries` flag.
- Provenance summary text length on rich graphs; mitigated by summarizing only returned items and deduplicating edge lines.
