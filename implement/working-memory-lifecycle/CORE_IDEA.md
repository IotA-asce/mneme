# Core Idea: Working Memory Lifecycle v1 (Stage 2 / M2.2)

## Problem Statement

Working memory tracks active context, but nothing bounds an "interaction": context never opens or closes around a conversation, and snapshots only persist when a caller remembers to call `persist_snapshot()`. Episode boundaries are invisible.

## Desired Outcome

A `ContextWindowManager` that opens a context window when an interaction begins (speech, person appearing, touch), keeps it alive while interaction events arrive, closes it after an idle timeout, and **automatically persists a working-memory snapshot at the close boundary**. Window transitions publish `world_state_update` events (`state_key="context_window"`), and closed windows are kept in a bounded history.

## User / Project Value

Interactions become first-class: each conversation gets a bounded context with a durable snapshot at its boundary — the hook the executive (M2.4) and future episodic encoding use to reason about "this interaction" versus "the previous one".

## Affected Systems

- `src/android_brain_memory/context_windows.py` (new), `__init__.py`
- `tests/test_context_windows.py` (new)
- `docs/memory/WORKING_MEMORY.md`, roadmap/status docs, memory entry

## Assumptions

- Interaction-relevant observation types: `speech_transcript`, `person_seen`, `touch`. Body health and sound direction alone do not start an interaction.
- The owning harness drives `tick()` (like the consolidation daemon) — no threads.

## Constraints

- Deterministic (injected clock); manager owns windows only — `WorkingMemory` content updates stay where they are.
- Publishes `world_state_update` state events only.

## Non-Goals

- Multi-party concurrent windows (one window at a time in V1).
- Automatic episode creation from windows (promotion pipeline owns episodes; a future increment may bridge them).

## Risks

- Idle timeout tuning; default 8s is bench-scale and configurable.
