# Implementation Plan

## Phase 1 — Retrieval Downranking

- `retrieval.py`: `_decay_penalty(meta)` — explicit numeric `decay.downrank` (clamped 0..1) wins; else 0.3 when `decay.accessibility == "downrank_candidate"`; else 0.0.
- Final score = weighted score × (1 − penalty); explanations gain `decay_penalty` and `score_before_decay`.

## Phase 2 — Storage Status Setters

- `storage.py`: public `set_episode_status(episode_id, status)` and `set_fact_status(fact_id, status)` with validation, `KeyError` on unknown IDs, and commit.

## Phase 3 — Decay Pass and Purge

- `decay.py`:
  - `DecayOptions(suppress_after_s=30d, min_retrievals_to_keep=1, suppress_summarized_episodes=True, suppress_superseded_facts=True, max_items=500)`.
  - `run_decay_once(store, options=None, *, now_s=None, bus=None, source="memory_decay") -> DecayReport`:
    - episodes: active + decay policy `covered_by_summary` + reference time (last retrieval, else episode end) older than threshold + retrieval count below keep threshold → `suppressed`,
    - facts: `superseded` + not `user_confirmed` + reference time older than threshold → `suppressed`,
    - publishes one `memory_lifecycle` decay event with the report.
  - `purge_memory(store, memory_id, memory_kind, *, reason, force=False, now_s=None)`: status → `purged`, meta provenance gains `purge: {reason, purged_ts}`; `user_confirmed` facts require `force=True`; unknown IDs raise `KeyError`.

## Phase 4 — Tests (written first)

- `tests/test_decay.py`: downranking order + explanation fields, explicit downrank override, suppression criteria (age/retrievals/policy each gating), user-confirmed immunity, purge tombstone + force gate, lifecycle event, status setter validation.

## Phase 5 — Docs and Status

- `docs/memory/DECAY.md` (new); `RETRIEVAL.md` decay factor; `CONSOLIDATION.md` "hook now consumed"; `MASTER_ROADMAP.md` M1.4; `REPO_STATUS.md`; memory entry + index.

## Validation

- `python -m pytest tests/test_decay.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Status setters → downranking → decay pass/purge → docs.

## Rollback

Revert decay module, retrieval penalty, status setters, tests, docs. No schema changes (statuses already exist).

## Definition of Done

- Decay outcomes deterministic and explainable; suppression reversible; purge explicit, reasoned, tombstoned; user-confirmed facts protected; full suite passes.
