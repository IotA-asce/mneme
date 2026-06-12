# Changes

## Interfaces

- `interfaces/msg/Fact.msg`: + `tags`, `supersedes_fact_id`; − `last_confirmed_at` (storage-only).
- `interfaces/msg/Episode.msg`: − `derived_fact_ids` (unimplemented); field order normalized to the model.
- `interfaces/msg/MemoryCandidate.msg`: + `source_type`, typed `features`; − `source_node`, `salience`, `ttl`.
- `interfaces/msg/MemoryQuery.msg`: + `fact_subject`, `fact_predicate`, `fact_object_text`, `fact_source_type`, `fact_status`, `trusted_internal`, `include_internal`; − `context_json` (model has no such field).
- `interfaces/msg/MemoryBundle.msg`: + `summaries`, `ranking_explanations_json`.
- `interfaces/msg/SalienceFeatures.msg` (new), `interfaces/msg/MemorySummary.msg` (new), `interfaces/msg/RuntimeEvent.msg` (new).
- `interfaces/srv/UpsertFact.srv`: + `conflict_report_json` in the response.

## Tests

- `tests/test_interface_alignment.py` (new): draft parser, per-message two-way alignment contracts with documented name mappings and derived-field exclusions, `UpsertFact.srv` conflict reporting check, JSON round-trips for `MemoryCandidate`, `Episode`, `Fact`, `MemoryQuery`, `MemoryBundle`, `RuntimeEvent`.

## Docs

- `docs/architecture/SERIALIZATION.md` (new): JSON wire contract and enforcement workflow.
- `docs/architecture/ROS_INTEGRATION_PLAN.md` (new): node boundary notes and phased future launch plan.
- `docs/IMPLEMENTATION_PLAN.md`: Phase 6 marked implemented (preparation only).
- `docs/architecture/ROADMAP.md`: "Current Safest Next Task" rewritten now that all phases are done.
- `docs/architecture/REPO_STATUS.md`: interface alignment and serialization contract recorded; stale "not implemented" entry removed.
- `docs/NODE_ARCHITECTURE.md`: cross-references added.

## Planning

- `implement/ros-integration-prep/` (CORE_IDEA, IMPLEMENT, RULES).

No Python source changes; this feature is contracts, tests, and documentation only.
