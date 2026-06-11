# Structured Fact Retrieval

Type: Feature
Date: 2026-06-11
Status: Complete

## Summary

Added deterministic structured fact retrieval:

- extended `Fact` with optional tags,
- extended `MemoryQuery` with structured fact filters,
- added `002_fact_tags.sql`,
- added structured fact search by subject, predicate, object text, source type, status, and tags,
- kept non-empty `query_text` retrieval compatible,
- ranked user-confirmed facts ahead of inferred facts when relevance is similar,
- excluded non-active facts from ordinary retrieval,
- warned when explicit status filters return non-active facts.

No embeddings, vector search, machine learning, or new dependencies were added.
