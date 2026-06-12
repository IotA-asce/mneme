# Stage 4 Live Perception Core Idea

## Problem

Stage 4 device inventory can detect cameras, microphones, and speakers, but Mneme still needs perception workers that can turn discovered devices into the same event shapes used by the simulated runtime.

## Desired Outcome

Add live-perception worker contracts for camera keyframes and speech transcripts, bounded storage hygiene, and simple fusion diagnostics without forcing heavyweight media or ASR dependencies into the base package.

## Affected Systems

- Runtime loop
- Peripheral discovery
- Memory promotion and raw trace storage
- World model
- CLI
- Documentation, roadmap, backlog, and project memory

## Constraints

- Fake/scripted backends remain deterministic for tests and CI.
- Live capture is opt-in.
- The base install must not add OpenCV, audio, VAD, or ASR dependencies.
- Workers publish observations only; they do not command skills, actuators, or executive behavior.
- Raw frames and transcripts preserve provenance and confidence.

## Non-Goals

- No bundled face model.
- No bundled local ASR model.
- No TTS or speaker playback.
- No continuous video or continuous raw audio storage.
- No cloud dependency.

## Risks

- Real capture quality depends on the configured local command.
- Host permissions can block camera/microphone access.
- Command adapters are intentionally generic and need per-machine setup for real media tools.
