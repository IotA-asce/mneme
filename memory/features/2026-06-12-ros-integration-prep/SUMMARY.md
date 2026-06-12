# Summary: ROS Integration Preparation

Date: 2026-06-12
Type: Feature
Status: Complete

Implemented the implementation plan's Phase 6 (prepare for ROS integration) as pure preparation — no ROS packages, bindings, or runtime changes:

- Aligned every `interfaces/` draft with the current Python domain models: `Fact.msg` gained `tags`/`supersedes_fact_id` (dropped storage-only `last_confirmed_at`), `Episode.msg` dropped unimplemented `derived_fact_ids`, `MemoryCandidate.msg` now carries `source_type` and typed `SalienceFeatures`, `MemoryQuery.msg` gained the structured fact filters and internal-access flags, `MemoryBundle.msg` gained `summaries` and `ranking_explanations_json`, and new `SalienceFeatures.msg`, `MemorySummary.msg`, and `RuntimeEvent.msg` drafts were added. `UpsertFact.srv` responses now include `conflict_report_json`.
- Added `tests/test_interface_alignment.py`: a contract test that parses the drafts and asserts two-way field alignment against `to_dict()` output under a documented mapping (dict fields ↔ `*_json`, time fields, derived-field exclusions), plus JSON round-trips for all transportable models.
- Documented the JSON serialization contract (`docs/architecture/SERIALIZATION.md`) and the node boundaries + phased future launch plan (`docs/architecture/ROS_INTEGRATION_PLAN.md`).

Exit criterion met: the memory core can be wrapped by future ROS nodes without changing domain models, and the contract test fails on any future drift.
