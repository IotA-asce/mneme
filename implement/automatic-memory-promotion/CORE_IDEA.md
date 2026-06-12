# Core Idea: Automatic Memory Promotion Pipeline (Stage 1 / M1.1)

## Problem Statement

The memory lifecycle pieces all exist but nothing connects them autonomously. Scenario replay publishes `memory_candidate` events, salience scoring decides what should happen, and `MnemeMemory.remember_candidate()` can store traces/episodes — but a caller must wire each step by hand. The roadmap's `observe → buffer → score → promote` segment is manual.

## Desired Outcome

- A `MemoryPromoter` runtime component subscribes to `memory_candidate` events on the local bus and drives storage automatically per the salience decision:
  - `echo_only` → no durable write (the in-memory echo buffer already holds the fragment),
  - `working_memory_candidate` → durable raw trace only,
  - `episode` → raw trace + episode,
  - `episode_and_semantic_candidate` → raw trace + episode + a semantic-candidate flag for the future fact extractor (M1.2).
- Every promotion decision is published as a new `memory_lifecycle` runtime event (topic `memory`) for observability (M1.5 foundation).
- A replayed scenario yields durable storage with no manual storage calls.

## User / Project Value

This turns the memory system from a library into a behaving subsystem: perception events become memories by themselves, deterministically, with every decision observable on the bus.

## Affected Systems

- `src/android_brain_memory/promotion.py` (new), `runtime.py` (new event kind + helper), `__init__.py` exports
- `tests/test_promotion.py` (new)
- `docs/memory/PROMOTION.md` (new), `docs/architecture/RUNTIME.md`, status/roadmap docs

## Assumptions

- `memory_candidate` event payloads carry `{"candidate": MemoryCandidate.to_dict()}` (the shape simulation already publishes).
- Salience scoring stays the single decision authority; the promoter maps decisions to storage actions and never overrides scores.

## Constraints

- Deterministic: same events in, same storage out. No threads, no new dependencies.
- The promoter publishes lifecycle state only; it never publishes intent, goals, or actuator events.
- Malformed candidate events are counted and skipped, never crash the bus dispatch.

## Non-Goals

- Fact extraction (M1.2 — the promoter only flags semantic candidates).
- Working-memory mutation (the existing WorkingMemory component already consumes the same events).
- Retention policy for raw traces (M1.4).

## Risks

- Double-scoring: the promoter scores to decide, `remember_candidate` re-scores internally. Scoring is deterministic and cheap, so identical results are guaranteed; noted as acceptable V1 cost.
- Event storms could write many traces; bounded by upstream scenario/perception rates in V1.
