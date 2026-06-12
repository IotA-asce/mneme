# Context

Roadmap Phase 4 was marked "implemented for facts and episodes" but explicitly deferred summaries, warnings, and provenance-summary tests. Consolidation (Phase 5) was already producing `memory_summary` rows that retrieval could not surface, which made consolidated knowledge unreachable.

Design decisions:

- Summaries reuse the existing ranking weights instead of getting their own table; a summary candidate has no entities or salience, timestamp prefers `end_ts` then `created_ts`.
- `MemoryBundle.summaries` holds JSON-friendly dicts rather than typed records to avoid a models→storage import cycle; `MemorySummaryRecord.to_dict()` defines the dict shape.
- The withheld-candidates warning is a count only — leaking withheld IDs or content would defeat the speakability policy.
- Conflict warnings reuse `get_fact_conflict_reports()` per returned statement group, so the warning fires both for explicitly retrieved conflicted facts and for active facts whose statement group has conflicted siblings.
- The provenance summary only walks chains for returned items (bounded by `max_results`), deduplicating edge lines for stable output.

The fact→episode→trace chain reads from the Phase 1 feature (`storage-provenance-read-apis`, merged the same day) are a hard dependency.
