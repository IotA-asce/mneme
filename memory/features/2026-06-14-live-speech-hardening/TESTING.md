# Testing

Focused verification:

```bash
.venv/bin/python -m pytest tests/test_speech_loop_hardening.py tests/test_conversational_presence.py tests/test_live_perception.py tests/test_stage6_local_living_lab.py -q
```

Result during implementation: 40 passed.

Final verification:

```bash
git diff --check
.venv/bin/python scripts/dev_check.py
```

Result during implementation: passed; `scripts/dev_check.py` completed DB init, smoke test, and 278 pytest tests.

Manual remaining validation:

- local microphone permission,
- faster-whisper model placement and latency,
- local TTS playback,
- barge-in during real speech,
- no duplicate spoken responses in a sustained local speech run.
