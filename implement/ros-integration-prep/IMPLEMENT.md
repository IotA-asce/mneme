# Implementation Plan

## Phase 1 — Contract Test (red)

- New `tests/test_interface_alignment.py`:
  - minimal `.msg` parser (field name extraction, comment/blank tolerant, `header` excluded),
  - explicit per-message mapping tables: msg field → model `to_dict()` key,
  - alignment asserted in both directions (no unmapped msg fields, no unmapped model keys, documented derived-field exclusions),
  - JSON round-trip tests for `RuntimeEvent`, `MemoryCandidate`, `Episode`, `Fact`, `MemoryQuery`, `MemoryBundle` through `json.dumps` + `from_dict`.

## Phase 2 — Interface Draft Alignment (green)

- `msg/Fact.msg`: add `tags`, `supersedes_fact_id`; drop storage-only `last_confirmed_at`.
- `msg/Episode.msg`: drop unimplemented `derived_fact_ids`.
- `msg/MemoryCandidate.msg`: align to the model (add `source_type`, typed `SalienceFeatures features`, `payload_json`; drop `source_node`, `salience`, `ttl`).
- `msg/SalienceFeatures.msg` (new): eight float32 feature fields.
- `msg/MemoryQuery.msg`: add structured fact filters and internal-access flags; drop unimplemented `context_json`.
- `msg/MemorySummary.msg` (new): summary record fields.
- `msg/MemoryBundle.msg`: add `summaries`, `ranking_explanations_json`.
- `msg/RuntimeEvent.msg` (new): event envelope matching `RuntimeEvent.to_dict()` minus derived `expires_at`.
- `srv/UpsertFact.srv`: add `conflict_report_json` to the response.

## Phase 3 — Documentation

- `docs/architecture/SERIALIZATION.md`: JSON wire contract (`to_dict`/`from_dict`, enum string values, timestamp units, `*_json` mapping rule, derived fields).
- `docs/architecture/ROS_INTEGRATION_PLAN.md`: node boundary notes (module → future node → topics → messages) and a phased future launch plan.
- Update `docs/IMPLEMENTATION_PLAN.md` Phase 6 status, `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`, `docs/NODE_ARCHITECTURE.md` cross-reference.

## Files Likely To Change

- `interfaces/msg/*.msg`, `interfaces/srv/UpsertFact.srv`
- `tests/test_interface_alignment.py` (new)
- `docs/architecture/SERIALIZATION.md`, `docs/architecture/ROS_INTEGRATION_PLAN.md` (new)
- `docs/IMPLEMENTATION_PLAN.md`, `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`, `docs/NODE_ARCHITECTURE.md`

## Validation

- `python -m pytest tests/test_interface_alignment.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Contract test (red) → draft alignment (green) → docs → status updates.

## Rollback

Revert interface drafts, the contract test, and docs. No code paths or persistence change.

## Definition of Done

- Contract test fails on drift and passes on the aligned drafts.
- Serialization contract and ROS integration plan documents exist.
- The memory core requires no domain model changes to be wrapped by future ROS nodes.
