# ROS 2 Integration Plan

Date: 2026-06-12
Status: **Deferred** — moved to the Stage 6 physical-embodiment track by owner decision (master roadmap revision 2). The interface contracts and node boundaries below remain the plan of record for when the physical track resumes; until then the cross-platform local runtime (Stage 3) is the transport. No ROS packages should be added before that track is green-lit.

This document records the node boundaries and the future launch sequence so that ROS 2 integration is a mechanical wrapping exercise, not a redesign.

## Principles

- ROS nodes wrap the existing Python modules; domain models and the memory engine do not change.
- The local `EventBus` topics map 1:1 onto ROS topic namespaces; the topic/kind boundary validation in `runtime.py` is the same boundary ROS QoS and namespaces will enforce.
- The architectural rule holds across transports: workers publish observations, state builders publish state, the executive publishes intent, skills publish actuator goals, the actuator bridge sends final commands, safety may override any stage.
- Serialization follows `docs/architecture/SERIALIZATION.md`.

## Node Boundary Notes

| Future node | Wraps module | Subscribes | Publishes | Interface drafts |
|---|---|---|---|---|
| `perception/*_worker` | `simulation.py` workers (later: real perception) | sensors | `/perception/*` (`RuntimeEvent` of kind `perception_observation`) | `RuntimeEvent.msg` |
| `working_memory_node` | `working_memory.py` | `/perception/*`, `/attention/*`, `/safety/*` | `/memory/candidates` (`MemoryCandidate`), working context snapshots | `MemoryCandidate.msg`, `SalienceFeatures.msg`, `srv/GetWorkingContext.srv` |
| `attention_manager_node` | `attention.py` | `/perception/*`, `/safety/*` | `/attention/updates` | `RuntimeEvent.msg` |
| `episodic_encoder_node` | `engine.py` (`remember_candidate`) | `/memory/candidates` | episode/trace writes (local store) | `Episode.msg` |
| `retrieval_manager_node` | `retrieval.py` | retrieval requests | `MemoryBundle` responses | `action/RetrieveMemory.action`, `MemoryBundle.msg`, `MemorySummary.msg`, `MemoryQuery.msg` |
| `semantic_extractor_node` | future fact extraction | episodes | `Fact` upserts | `srv/UpsertFact.srv`, `Fact.msg` |
| `consolidation_daemon_node` | `consolidation.py` | schedule/idle triggers | summaries, decay metadata | `action/ConsolidateMemory.action` |
| `executive_node` | `executive.py` | `/attention/*`, `/memory/*`, `/safety/*`, working context | `/executive/intent` | `RuntimeEvent.msg` |
| `safety_supervisor_node` | future | everything | `/safety/*` overrides | `RuntimeEvent.msg` |

Boundary rules that must survive the transport change:

- Memory nodes never publish to `/skill/*` or actuator topics; memory never controls motors.
- Perception events cannot masquerade as executive intent — `RuntimeEvent` kind/topic validation is the contract.
- The executive publishes intent only; skill controllers (future) own actuator goals; the actuator bridge (future) owns final commands.
- The SQLite store stays owned by a single memory service process; other nodes go through services/actions, never the file.

## Future Launch Plan (phased)

1. **Replay bench (no ROS)** — current state: scenario replay drives echo/working memory, attention, and executive over the local bus. Keep this as the regression harness forever.
2. **Single-process ROS bridge** — one `mneme_memory_node` wrapping `MnemeMemory`, exposing `RetrieveMemory.action`, `UpsertFact.srv`, `GetWorkingContext.srv`. Local bus stays internal; ROS is an adapter at the edge only.
3. **Split state nodes** — `working_memory_node`, `attention_manager_node`, `executive_node` as separate processes once the single-process bridge is stable under replay-driven integration tests.
4. **Perception onboarding** — real perception workers publish `/perception/*`; simulated workers remain available behind the same topics for CI.
5. **Skills and actuation (gated)** — skill controllers and the actuator bridge join only with the safety supervisor present, dry-run/fake actuator backends first, per `AGENTS.md` safety rules.

Each phase requires: replay tests passing against the new topology, no domain model changes, and a project memory entry recording the topology decision.

## Verification Today

- `tests/test_interface_alignment.py` keeps models and interface drafts aligned.
- `tests/test_runtime_events.py` enforces the kind/topic boundaries the ROS namespaces will mirror.
- Scenario replay (`docs/runbooks/SCENARIO_REPLAY.md`) is the integration harness every future phase must keep green.
