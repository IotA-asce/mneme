# ADR 0001 — Memory-first V1

## Decision

The first implementation will focus on the memory subsystem and will not require real robot hardware or ROS 2.

## Reason

Memory defines continuity and context. It can be implemented and tested locally before perception and motor systems are ready.

## Consequences

- Faster development start.
- Easier Codex-driven implementation.
- Clear boundary between memory and future robotics runtime.
- Real-time and motor safety are deferred to later integration phases.
