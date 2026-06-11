# Risks

- Object-value matching is currently JSON text matching, not schema-aware object querying.
- Tag filtering requires migration `002_fact_tags.sql`; older databases without that table return no tag-filtered matches.
- Source priority is retrieval ordering only. It does not implement conflict detection, user confirmation workflows, or automatic supersession.
- Retrieval still does not update meta-memory retrieval counters.
