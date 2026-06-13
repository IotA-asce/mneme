# Testing

Focused verification:

```bash
.venv/bin/python -m pytest tests/test_conversational_presence.py tests/test_live_perception.py tests/test_speech_loop_hardening.py -q
git diff --check
.venv/bin/python scripts/dev_check.py
```

Result during implementation: 24 passed.

Final verification:

```bash
git diff --check
.venv/bin/python scripts/dev_check.py
```

Result during implementation: passed; `scripts/dev_check.py` completed DB init, memory smoke test, and 281 pytest tests.

Manual remaining validation:

- Run `mneme run --profile local-lab --live --json` on the current Mac and confirm status lines appear during the run.
- Run local vision with `--face-backend mediapipe` after optional dependencies are installed and camera permission is granted.
- Fix or provide the local ASR model path, then validate that speech transcripts produce dialogue and virtual speech output.
