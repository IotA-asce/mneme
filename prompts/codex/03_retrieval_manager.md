# Codex Prompt 03 — Retrieval Manager

Implement Phase 4 retrieval improvements.

Focus on:

- `MemoryQuery`
- `MemoryBundle`
- structured fact + episode retrieval
- reranking using relevance, recency, salience, confidence, and source type
- provenance summary in response

Add tests showing that:

- user-confirmed facts rank above inferred facts
- recent high-salience episodes are returned for topic queries
- empty retrieval gives a clear no-result bundle
