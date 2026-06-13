# Live Console Presence Implementation

## Changes

- Add live status rendering to `mneme run --live`.
- Route live status to stderr when `--json` is active.
- Add `--quiet-live-status` for machine-only output.
- Summarize camera frames, person observations, speech transcripts, ASR failures, attention target, and virtual presence state.
- Add tests for speech and vision live status while keeping JSON parseable.

## Validation

```bash
.venv/bin/python -m pytest tests/test_conversational_presence.py tests/test_live_perception.py tests/test_speech_loop_hardening.py -q
git diff --check
.venv/bin/python scripts/dev_check.py
```

## Definition of Done

- `mneme run --profile local-lab --live --json` shows live status immediately.
- `--json` remains valid stdout.
- User can see when the camera is working, when person detection is off, and when ASR fails.

