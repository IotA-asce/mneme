# Executive v0 Core Idea

## Problem statement

Mneme has runtime events, working memory, attention state, and safety events, but no executive layer that arbitrates high-level intent. Without this boundary, future skills could be tempted to infer action directly from attention or perception.

## Desired outcome

Add a deterministic Executive v0 that consumes working, attention, world, and safety state and emits high-level `executive_intent` events only.

## User/project value

This establishes the decision boundary between state builders and future skills while preserving the architecture rule that the executive publishes intent and skills publish actuator goals.

## Affected systems

- Local runtime event bus
- Working memory pending-response intent updates
- Attention state consumption
- Safety/degraded-mode coordination
- Future skill interfaces

## Assumptions

- V0 is deterministic and rule-based.
- Only one selected intent is emitted per evaluation.
- Safety rules outrank social interaction.
- No skill or actuator execution occurs in this phase.

## Constraints

- No LLM calls.
- No behavior tree dependency.
- No hardware commands.
- JSON-friendly models for future runtime adapters.

## Non-goals

- Dialogue generation.
- Skill scheduling.
- Gaze or motion control.
- Long-running autonomous planning.
- ROS 2 integration.

## Risks

- Rule priorities are early heuristics.
- Explicit memory instructions are detected with simple text matching.
- Intent publication can be refined later to reduce repeated identical intent events.
