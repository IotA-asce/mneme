# Core Idea: Forgetting and Decay Policy (Stage 1 / M1.4)

## Problem Statement

Consolidation writes decay hints (`provenance_json["decay"]`) but nothing consumes them: retrieval ranks decayed memories as if fresh, nothing ever becomes harder to retrieve or suppressed, and there is no explicit purge path. The lifecycle's `decay/suppress/forget` tail is missing.

## Desired Outcome

Staged forgetting, deterministic at every step:

1. **Accessibility decay (retrieval-time)**: memories with decay metadata are downranked — score multiplied by `(1 - penalty)`, with the penalty visible in ranking explanations.
2. **Suppression (decay pass)**: `run_decay_once()` marks old, summarized, rarely-retrieved episodes and old superseded facts as `suppressed` (hidden from ordinary retrieval, fully recoverable, provenance intact).
3. **Purge (explicit only)**: `purge_memory()` sets status `purged` and records a reason in meta-memory provenance as a tombstone — rows are preserved, nothing is deleted, and user-confirmed facts require `force=True`.

All decay actions publish `memory_lifecycle` events (`lifecycle_stage="decay"`).

## User / Project Value

Memory stops being append-only-forever: repeated trivia fades behind its summary, superseded beliefs stop resurfacing, and forgetting is always explainable, reversible (except explicit purge), and auditable.

## Affected Systems

- `src/android_brain_memory/decay.py` (new), `retrieval.py` (penalty), `storage.py` (status setters), `__init__.py`
- `tests/test_decay.py` (new)
- `docs/memory/DECAY.md` (new), `docs/memory/RETRIEVAL.md`, `docs/memory/CONSOLIDATION.md`, roadmap/status docs

## Assumptions

- Decay metadata shape from consolidation: `{"policy": "covered_by_summary", "accessibility": "downrank_candidate", "summary_id": ..., ...}`; an explicit numeric `downrank` key (0..1) is also honored.
- Suppressed/purged statuses already exist in the schema and are already excluded from ordinary retrieval by the active-status default.

## Constraints

- Never auto-suppress or auto-purge `user_confirmed` facts; purging one requires an explicit `force=True` with a reason.
- Suppression requires *all* of: decay/supersession state, age beyond threshold, and retrieval count below the keep threshold.
- Purge is a tombstone: status + provenance note. No row deletion, no content rewriting in V1.
- Deterministic: the pass takes `now_s` injection; no wall-clock reads in logic paths.

## Non-Goals

- Detail decay (content summarization-in-place) — future work, documented.
- Automatic purge scheduling — purge stays caller-explicit in V1.
- Retention policy for raw traces (tracked separately in the backlog).

## Risks

- Over-aggressive suppression hides useful memories; mitigated by conservative defaults (30-day threshold, any retrieval keeps an episode) and full reversibility.
- Score multiplier interacts with ranking weights; mitigated by exposing `score_before_decay` and `decay_penalty` in explanations and pinning order in tests.
