# Summary: Retrieval Warnings, Summary Retrieval, and Derived Provenance Summaries

Date: 2026-06-12
Type: Feature
Status: Complete

Closed the remaining roadmap Phase 4 (retrieval ranking) gaps:

- Memory summaries are now retrievable: text queries search `memory_summary` rows (summary text + scope key), rank them with the existing weighted factors, and return them in the new `MemoryBundle.summaries` list with ranking explanations, `max_results` caps, speakability filtering, and retrieval-history updates.
- Deterministic retrieval warnings: empty results, speakability-withheld candidate counts (content never leaked), explicit non-active status filters (existing), and conflicting fact statement groups.
- `MemoryBundle.provenance_summary` is now derived from stored provenance chains (`get_provenance_chain`) for returned items instead of a hardcoded sentence, with an explicit fallback when no links exist.

Storage gained `search_memory_summaries()`; `MemorySummaryRecord` gained `to_dict()`. Two existing test assertions that encoded the old hardcoded provenance string and the warnings list were updated to the new intended behavior.
