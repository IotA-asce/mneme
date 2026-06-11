# Retrieval Reranking

Type: Feature
Date: 2026-06-11
Status: Complete

## Summary

Added deterministic retrieval reranking for facts and episodes:

- introduced retrieval candidates and ranked candidates,
- applied the documented weighted factors,
- used `MemoryQuery.entities` for entity matching,
- used meta-memory retrieval count as an optional history bonus,
- added `MemoryBundle.ranking_explanations`,
- added tests for deterministic ranking order and explanation payloads,
- documented the ranking behavior in `docs/memory/RETRIEVAL.md`.

No vector database, embeddings, LLM reranking, machine learning, or new dependencies were added.
