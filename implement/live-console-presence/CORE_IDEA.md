# Live Console Presence Core Idea

## Problem

Live mode could run perception workers while looking silent. With `--json`, output was buffered until exit, so camera frames, ASR failures, attention changes, and presence state were hidden inside the final JSON dump.

## Desired Outcome

Make live mode visibly active while preserving machine-readable JSON:

- stream human-readable perception/attention/speech/presence lines,
- keep final `--json` output parseable,
- explain common setup gaps such as disabled face detection or ASR model path errors,
- avoid pretending camera observations are dialogue.

## Constraints

- No new dependencies.
- No autonomous speech from vision alone.
- No direct perception-to-actuator shortcuts.
- JSON stdout must remain valid when `--json` is used.

