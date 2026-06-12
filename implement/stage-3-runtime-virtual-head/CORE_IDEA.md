# Stage 3 Runtime and Virtual Head Core Idea

## Problem statement

Stages 0-2 implemented memory lifecycle, world state, attention, executive, dialogue, and deterministic replay pieces, but they were not available as one runnable local program.

## Desired outcome

Add a cross-platform Stage 3 runtime that wires the existing cognition stack in one process, discovers peripherals through a fake deterministic backend, and exposes a terminal virtual head through `mneme run`.

## User/project value

This turns the bench cognition stack into a runnable virtual-head loop without waiting for camera, microphone, speaker, ROS, or hardware dependencies.

## Affected systems

- Runtime event bus
- Memory engine and lifecycle components
- World model
- Sensory echo and working memory
- Context windows
- Attention manager
- Executive
- Dialogue planner
- CLI packaging

## Assumptions

- Stage 3 uses typed terminal input, not real ASR.
- Peripheral discovery is fake and deterministic for CI.
- No domain model changes are required.
- The local event bus remains the runtime transport.

## Constraints

- No camera, microphone, speaker, ROS, actuator, GPIO, serial, or hardware libraries.
- No LLM calls.
- Keep the runtime deterministic under tests.
- Keep platform-specific code out of Stage 3.

## Non-goals

- Real perception.
- Spoken TTS.
- Visual avatar rendering.
- Skill controllers or actuator bridge.
- Hardware safety certification.

## Risks

- Stage 3 proves runtime wiring, not live perception quality.
- The terminal virtual head is intentionally minimal.
- Device discovery is a contract and test scaffold until Stage 4 adds real backends.
