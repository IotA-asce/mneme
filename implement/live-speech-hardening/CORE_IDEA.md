# Live Speech Hardening Core Idea

## Problem

Mneme has local speech worker seams, virtual speech skills, and barge-in behavior, but the speech loop did not expose enough structured diagnostics to tell whether a live run was healthy. Duplicate live transcripts, no-speech captures, ASR failures, TTS failures, latency, and stuck speaking states needed deterministic fake-backed coverage before real microphone validation.

## Desired Outcome

Make live speech behavior auditable and repeatable without changing the architecture:

- perception still publishes `speech_transcript`,
- executive/dialogue still choose responses,
- virtual skills still own speech output,
- diagnostics observe the flow and report status.

## Value

This makes the Local Living Lab safer to use daily because failures become visible JSON state instead of silent behavior. It also gives future real-device testing a baseline suite that does not require a microphone, ASR model, or speaker in CI.

## Affected Systems

- Runtime snapshots and event handling.
- Live speech worker reports.
- Virtual speech skill status metadata.
- Evaluation logging.
- `mneme eval` CLI.
- README/runbook/status documentation.

## Constraints

- No new required dependencies.
- No cloud services.
- No real hardware control.
- No direct speech-to-actuator shortcuts.
- Real mic/ASR/TTS validation remains manual.

## Non-Goals

- Replacing the dialogue planner.
- Adding VAD tuning or a new ASR engine.
- Adding private-log redaction.
- Implementing a graphical avatar.
- Physical embodiment or ROS integration.

## Risks

- Fake-backed soak fixtures prove runtime behavior, not local model quality or device permissions.
- Duplicate suppression uses a short deterministic window and may need tuning after real sessions.
- Latency fields are observable but not yet summarized as histograms.

