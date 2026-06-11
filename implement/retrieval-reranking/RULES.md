# Rules

## Architectural Boundaries

- Retrieval ranks memory records but does not create, modify, confirm, suppress, purge, or actuate from them.
- Storage remains the owner of SQLite access.
- The ranking layer must remain deterministic and inspectable.

## Ranking Rules

- Use explicit weights from the design document.
- Keep factor values normalized to `0.0..1.0`.
- Use deterministic tie-breaks after score.
- User-confirmed source reliability should remain stronger than inferred source reliability.

## Compatibility Rules

- Preserve `retrieve_memory(store, query)`.
- Preserve existing `MemoryBundle` fields.
- Add debug data through optional fields only.

## Testing Expectations

- Test ranking order.
- Test explanation contents.
- Test meta-memory retrieval history bonus.
- Keep structured fact and query-text retrieval tests passing.

## Anti-Patterns

- Do not add vector search.
- Do not call an LLM for reranking.
- Do not silently mutate retrieval history counters in this phase.
- Do not let retrieval bypass executive or safety architecture.
