# Roadmap

Date: 2026-06-13
Status: V1 memory prototype roadmap — all phases complete; current work moved to Stage 6 Local Living Lab

This document records the V1 memory prototype phases. For the full implementation path from the completed memory core to the finished android head, see `docs/architecture/MASTER_ROADMAP.md`.

This roadmap orders the next work by safety and dependency. Mneme should remain bench-only and memory-first until the storage, retrieval, provenance, and consolidation contracts are testable.

## Phase 0 — Verified Starter Baseline

Status: mostly complete.

Already present:

- Package skeleton, SQLite migration, scripts, tests, docs, config, and interface drafts.
- Tracked migration runner with checksum audit.
- Salience scoring with explicit remember override.
- Raw trace, episode, and fact writes.
- Meta-memory and working context snapshot storage methods.
- Fact and episode ID lookups.
- Basic text retrieval over facts and episodes.
- Conservative non-mutating consolidation placeholder.
- High-level memory facade and JSON CLI for local debug/replay workflows.
- Local runtime event model and deterministic in-process event bus for ROS-like tests and demos.
- Bounded sensory echo and working memory components integrated with local runtime events.
- Deterministic simulated perception workers and scenario replay fixtures.

Remaining baseline cleanup:

- Keep status documents and backlog aligned with implemented behavior.
- Add raw trace read/list and fact support read APIs before expanding retrieval behavior.
- Avoid treating interface drafts as runtime ROS integration.
- Consider a package console-script entry point after CLI command shape settles.
- Keep local runtime events adapter-free until the event boundaries stabilize.
- Add durable promotion flows only after replay, echo, and working-memory behavior remains stable under tests.

## Phase 1 — Storage and Provenance Baseline

Goal: make stored memories inspectable and provenance-preserving without changing the schema.

Status: Implemented.

Deliverables:

- [x] Read APIs for raw traces and fact support links.
- [x] Episode time-window retrieval.
- [x] Meta-memory writes for raw traces, episodes, facts, and summaries.
- [x] Speakability filtering for ordinary retrieval.
- [x] Retrieval count updates for returned records.
- [x] Provenance summary generation from stored trace, episode, and fact support data (`get_provenance_chain`).

Exit criteria:

- [x] A stored candidate can be traced from raw trace to episode to fact support.
- [x] Tests prove support links can be read directly.
- [x] No new dependencies are introduced.

## Phase 2 — Structured Fact Retrieval

Goal: move beyond simple free-text lookup while preserving the current simple API.

Status: Implemented for facts. Episode time-window retrieval is implemented (`get_episodes_in_window`); topic-specific episode retrieval remains future work.

Deliverables:

- [x] Fact lookup by subject, predicate, and optional object/topic text.
- [x] Tests for user-confirmed and inferred fact retrieval.
- [x] Clear behavior for active versus superseded/conflicted/suppressed statuses.
- [x] Backward-compatible `retrieve_memory()` behavior over the new structured storage methods.

Exit criteria:

- [x] A topic/person query can return relevant facts without relying only on JSON substring matching.
- [x] Retrieval results preserve source type and confidence.

## Phase 3 — Conflict and Meta-Memory

Goal: implement the truth/provenance rules documented in the design.

Deliverables:

- [x] Meta-memory writes for stored episodes and facts.
- [x] Basic conflict detection for facts with the same subject/predicate and incompatible object values.
- [x] User-confirmed fact precedence over inferred facts during conflict/supersession decisions.
- [x] Supersession/conflict status tests.

Exit criteria:

- [x] Conflicts are marked rather than silently overwritten.
- [x] User-confirmed facts are preferred during conflict/supersession decisions.

## Phase 4 — Retrieval Ranking

Goal: make retrieval cue-based while staying local and deterministic.

Status: Implemented for facts, episodes, and memory summaries.

Deliverables:

- [x] Reranking based on context match, entity match, recency, salience, confidence, source type, and retrieval history where available.
- [x] Use of `MemoryQuery.entities`; `MemoryQuery.tags` is already supported for fact retrieval.
- [x] Retrieval warnings for empty, suppressed, or conflicting memory results.
- [x] Summary retrieval and ranking through `MemoryBundle.summaries`.
- [x] Tests for rank order and ranking explanations.
- [x] Tests for provenance summary derived from stored support links.

Exit criteria:

- [x] Retrieval order is explainable and tested.
- [x] Queries for the same topic/person return stable, relevant bundles.

## Phase 5 — Minimal Consolidation

Goal: create useful summaries without pretending to have a full daemon.

Deliverables:

- [x] `memory_summary` writes for repeated or high-salience episodes.
- [x] A deterministic repeated-event grouping placeholder.
- [x] Decay/downranking fields or documented schema changes if current tables are insufficient.
- [x] Consolidation report tests.

Exit criteria:

- [x] Repeated events can produce one summary artifact.
- [x] The consolidation pass remains safe, local, and deterministic.

## Deferred Until V1 Memory Is Stable

Do not start these until the memory core is demonstrably stable:

- ROS 2 runtime packages and launch files.
- Real camera, microphone, touch, or body-state integrations.
- Hardware actuation, GPIO, serial, servo control, or firmware flashing.
- LLM-backed summarization or autonomous procedural memory.
- Vector databases or cloud storage.

## Current Safest Next Task

All V1 roadmap phases (0–5) and the implementation plan's Phase 6 (ROS preparation) are implemented. Stages 3–5 of the master roadmap are also complete, and Stage 6 now means **Local Living Lab** rather than physical embodiment.

The safest next work, in dependency order:

1. Validate `mneme run --profile local-speech` on the current machine with real microphone permission, local ASR model files, local TTS playback, barge-in, and duplicate-response checks.
2. Validate `mneme run --profile local-vision` with real camera permission, OpenCV frame capture, MediaPipe face/person observations, and anonymous-session continuity.
3. Improve `mneme ui` from a debug dashboard toward a useful local virtual head while keeping cognition owned by the runtime.
4. Convert real local runs into redacted soak scenarios and daily-driver evaluation logs.
5. Continue memory/retrieval polish such as topic-specific episode retrieval, conflict-resolution workflows, and person-scoped continuity review.

Physical hardware, ROS runtime integration, actuation, GPIO, serial, PWM, firmware flashing, and motors remain deferred behind the safety rules in `AGENTS.md`.
