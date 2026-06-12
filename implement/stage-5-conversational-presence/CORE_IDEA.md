# Stage 5 Conversational Presence Core Idea

## Problem

Mneme could already perceive typed/live transcript events, remember, attend, generate executive intent, and plan text responses. It did not yet have a runtime layer that made those plans feel like a virtual presence: speaking, showing expression state, handling interruptions, or exposing virtual skill status.

## Desired Outcome

Stage 5 turns the local virtual head into a deterministic conversational presence:

- utterance plans become virtual speech goals,
- simulated speech is recorded for JSON/replay,
- optional local TTS commands can play speech,
- avatar state tracks listening, thinking, speaking, idle, gaze, and safety,
- user speech can interrupt active virtual speech,
- virtual skills use the same event contracts future physical skills can consume.

## Project Value

This proves the social timing and skill boundary before any physical embodiment. Mneme can now be used as a local virtual assistant while preserving the architecture rule that the executive publishes intent and skills publish status.

## Affected Systems

- Runtime loop
- Dialogue planner output consumption
- Virtual head CLI
- Procedural memory for speech voice selection
- Runtime events (`skill_goal`, `skill_status`)
- Documentation, roadmap, backlog, and project memory

## Assumptions

- Local TTS, if used, is supplied by the host machine as an external command.
- The default path remains deterministic and does not play audio.
- Avatar state is JSON/debug state, not a graphical renderer.

## Constraints

- Do not add a native TTS, audio, GUI, or hardware dependency.
- Do not command physical hardware.
- Do not let speech output bypass executive intent, dialogue planning, or skill status events.
- Keep tests deterministic through injected clocks and simulated backends.

## Non-Goals

- Graphical avatar UI.
- Native ASR/TTS engines.
- Speaker-device routing beyond the placeholder contract.
- Physical skill controllers, actuator bridge, ROS runtime, or motor behavior.

## Risks

- A host TTS command can fail or block; command adapters must timeout and report failed virtual skill status.
- Simulated completion does not prove real speech timing or hardware safety.
- Duplicate executive intents can occur during runtime event cascades; virtual speech must avoid duplicate output.
