# Rules

## Architecture

- Consolidation may read episodes and write summaries/meta-memory.
- Consolidation must not command behavior or touch hardware.
- Consolidation must not bypass retrieval status/speakability rules.

## Persistence

- Do not delete source episodes.
- Do not change episode status in this phase.
- Store decay/downranking hints in meta-memory unless a future migration is explicitly justified.
- Use deterministic summary IDs for repeatable manual runs.

## Grouping

- Prefer deterministic local cues over model judgment.
- Use context tags, participants, topic tokens, and time buckets.
- Avoid LLM summarization.

## Testing

- Test repeated events producing one summary.
- Test source episodes remain active.
- Test decay/downranking metadata is written.

## Non-Goals

- No fact extraction.
- No purge behavior.
- No scheduler.
- No vector search or embeddings.
