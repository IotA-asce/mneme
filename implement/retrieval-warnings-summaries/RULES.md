# Rules

## Architectural Boundaries

- Retrieval stays deterministic and local: no embeddings, no LLM reranking, no new dependencies.
- Storage owns SQL; retrieval owns candidate building, ranking, warnings, and bundle assembly.
- Warnings surface conditions; they must not trigger conflict resolution, deletion, or status changes.

## Safety Constraints

- Speakability policy must keep applying to summaries exactly as it does to facts and episodes.
- The withheld-candidates warning may state a count but must never include withheld content or IDs.

## Testing Expectations

- Tests written before implementation (red first).
- Cover: summary text search, ranked summary inclusion and `include_summaries=False`, retrieval counter updates for summaries, empty-result warning, speakability-withheld warning, conflict warning, provenance summary derived from support links, bundle round-trip with summaries.

## Performance Constraints

- Provenance summary generation only for returned items (bounded by `max_results`), not all candidates.

## Persistence / Migration Rules

- No schema changes; `memory_summary` and `meta_memory` tables are used as-is.

## Anti-Patterns

- Do not add summary-specific ranking weight tables yet (premature).
- Do not leak withheld memory content into warnings or explanations.
- Do not make warning text depend on dict iteration order or wall-clock time.

## What Must Not Change

- Existing fact/episode retrieval results and ranking order for current tests.
- `MemoryBundle` existing field semantics; `summaries` is additive.
- Speakability filtering defaults.
