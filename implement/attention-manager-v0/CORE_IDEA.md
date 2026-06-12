# Attention Manager v0 Core Idea

## Problem statement

Mneme has local runtime events, simulated perception workers, sensory echo, and working memory, but no dedicated component that decides what currently matters. Without an attention manager, downstream skills would be tempted to infer focus directly from raw perception events.

## Desired outcome

Add a deterministic local Attention Manager that listens to runtime events, ranks candidate focus targets, and publishes attention state through the existing `attention_update` runtime boundary.

## User/project value

This gives the robot head architecture a clear "what matters now" layer before gaze, expression, dialogue, or memory behavior try to act on perception.

## Affected systems

- Local runtime event bus
- Working memory attention target updates
- Simulated perception replay compatibility
- Future skill/executive integration

## Assumptions

- V0 uses deterministic scoring only.
- Perception events may carry heterogeneous JSON payloads.
- Attention state is not an actuator command.
- Safety-relevant targets may override ordinary social focus.

## Constraints

- Do not add ROS or asyncio.
- Do not implement gaze control.
- Keep models JSON-friendly and testable.
- Preserve runtime boundaries: attention publishes state only.

## Non-goals

- Real camera, microphone, or motor integration.
- LLM attention planning.
- Long-term attention learning.
- Multi-modal identity fusion beyond simple target IDs.

## Risks

- Deterministic weights are early heuristics and may need tuning.
- Target identity is simple and may need a world-model adapter later.
- Dwell/lock behavior should remain conservative until real timing data exists.
