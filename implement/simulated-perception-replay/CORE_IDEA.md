# Simulated Perception Replay Core Idea

Date: 2026-06-12
Status: Implemented in this feature branch

## Problem

Mneme has a local runtime event bus, sensory echo, and working memory, but no deterministic way to feed realistic perception-like event sequences through those components. The project needs replayable scenarios before any real camera, microphone, touch, or health sensor integration.

## Desired Outcome

Add simulated perception workers and a scenario replay runner that can publish local runtime events for:

- face/person observation,
- speech transcript,
- sound direction,
- touch,
- body/internal health.

Scenarios should be stored as YAML or JSON fixtures, replayed deterministically, and able to emit memory candidate events for important steps.

## Project Value

- Gives tests and demos a repeatable perception-to-memory path.
- Exercises event bus, sensory echo, working memory, and memory candidate boundaries.
- Prepares the repo for ROS-like runtime architecture without ROS or real sensors.

## Constraints

- No real camera, microphone, audio, or touch integration.
- No OpenCV, Whisper, or audio libraries.
- No ROS 2.
- No asyncio.
- No new dependencies beyond existing PyYAML.
- Deterministic timestamps and event order.

## Non-Goals

- No sensor drivers.
- No media processing.
- No autonomous perception model inference.
- No durable storage writes during replay unless a future caller explicitly adds them.

## Risks

- Scenario payloads can become too loose if not documented.
- Replay should not imply sensor realism or hardware safety.
- Memory candidate generation should remain explicit, not a hidden inference step.
