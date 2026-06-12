# Implementation Plan

## Phase 1 — Self Model

- `self_model.py`: `SelfModel(engine, subject="self")`:
  - `set_identity_fact(predicate, value, source_type=system_generated, confidence=0.9, notes=None)` — fixed fact ID per predicate (`fact_self_<predicate-slug>`), in-place update via upsert,
  - `get_identity(predicate)`, `identity_facts()` (active, sorted by predicate), `describe()` deterministic text summary.

## Phase 2 — Procedural Memory

- `ProceduralMemory(engine, subject="self")`:
  - `set_parameter(skill, parameter, value, confidence=0.9, reason=None)` — versioned facts `fact_proc_<skill>_<param>_v<N>` with predicate `procedure:<skill>:<parameter>`, object `{value, version, skill, parameter}`, `supersedes_fact_id` chaining to the prior version which is marked superseded; provenance notes carry the reason,
  - `get_parameter(skill, parameter, default=None)` — latest active value,
  - `parameter_history(skill, parameter)` — all versions ordered,
  - `parameters_for_skill(skill)` — `{parameter: value}` mapping.

## Phase 3 — Tests (written first)

- `tests/test_self_model.py`: identity create/read/in-place update, retrieval integration, describe text, parameter versioning + supersession chain + history + provenance notes, defaults, per-skill mapping.

## Phase 4 — Docs

- `docs/memory/SELF_MODEL.md` (new); `MASTER_ROADMAP.md` M2.6 + Stage 2 closeout; `REPO_STATUS.md`; memory entry + index.

## Validation

`python -m pytest tests/test_self_model.py` → full suite → dev_check.

## Rollback

Revert new module/tests/docs; additive, no schema changes.

## Definition of Done

Self-queries answerable from memory; procedural parameters versioned with provenance; full suite passes; Stage 2 closed.
