# Sensory Echo and Working Memory Core Idea

Date: 2026-06-12
Status: Implemented in this feature branch

## Problem

Mneme has durable memory storage, a local runtime event bus, and working-context snapshots, but no active in-process components for the two earliest memory layers:

- sensory echo buffer,
- working memory.

The design calls for recent event fragments and a small explicit active context before durable promotion and retrieval.

## Desired Outcome

Add local, deterministic runtime components:

- `SensoryEchoBuffer` stores recent runtime event fragments with TTL, source metadata, confidence, sequence, and payload.
- `WorkingMemory` maintains bounded active context: current speaker, topic, attention target, recent dialogue turns, active goal, safety state, and pending response intent.
- Both components can subscribe to the local `EventBus`.
- Working memory can export JSON snapshots and optionally persist them through `MemoryStore.store_working_context_snapshot()`.

## Project Value

- Makes the memory lifecycle concrete before durable storage.
- Provides a local test/demo layer without camera, microphone, ROS, or hardware integration.
- Keeps working memory intentionally small instead of turning it into a chat log.

## Constraints

- No real sensor integration.
- No ROS 2.
- No asyncio.
- No new dependencies.
- Keep tests deterministic with explicit timestamps.
- Preserve lower-level memory modules.

## Non-Goals

- No perception workers.
- No autonomous promotion from echo to episodic/semantic memory.
- No durable event log.
- No full working-memory state manager outside this bounded V1 component.

## Risks

- Working memory can become an unbounded log if dialogue/event retention is not capped.
- Echo fragments can outlive their usefulness if TTL is ignored.
- Event payload conventions must remain documented because they are still JSON dictionaries in V1.
