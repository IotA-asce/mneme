# Context

The design document already described retrieval ranking factors, and structured fact retrieval was implemented before this change. Retrieval still returned storage-ordered facts and episodes, which made ranking behavior hard to inspect.

This work adds deterministic reranking while preserving the public `retrieve_memory(store, query)` entry point and the existing facts/episodes bundle fields.
