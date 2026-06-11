# Implementation Plan

## Phase 1 — Configurable Scoring

- Add `PromotionThresholds` and `SalienceScoringConfig`.
- Add `load_salience_config()`.
- Keep `score_candidate(candidate)` default behavior unchanged.
- Allow `score_candidate()` to accept config objects, config paths, custom weights, and custom thresholds.

## Phase 2 — Explanation Payload

- Add `SalienceResult.explanation`.
- Include feature values, raw feature values, weighted components, thresholds, raw score, final score, threshold band, decision, override reason, and clamped features.

## Phase 3 — Tests and Docs

- Cover threshold boundaries.
- Cover explicit remember override.
- Cover config loading.
- Cover custom thresholds.
- Cover defensive feature clamping.
- Add `docs/memory/SALIENCE.md`.

## Rollback

Revert salience code, salience tests, salience docs, and the `SalienceResult.explanation` field if callers need the previous minimal result shape.

## Definition of Done

- Existing scripts and tests pass.
- New salience boundary tests pass.
- Default scoring remains compatible.
- Documentation, backlog, and memory are updated.
