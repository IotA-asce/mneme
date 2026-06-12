# Testing

Planned and run for this change:

- `python -m pytest tests/test_stage6_local_living_lab.py tests/test_conversational_presence.py tests/test_live_perception.py`
- `python scripts/dev_check.py`
- `mneme models list --json`
- `mneme models verify --json`
- `mneme run --json --profile default --input "hello Mneme" --evaluation-log /tmp/mneme-stage6-eval.jsonl`
- `mneme eval summarize --path /tmp/mneme-stage6-eval.jsonl --json`

Real camera, microphone, ASR model, TTS model, and MediaPipe validation remain manual Local Living Lab checks.
