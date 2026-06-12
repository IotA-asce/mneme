# Testing

Planned verification:

```bash
python -m pytest tests/test_conversational_presence.py tests/test_stage3_runtime.py tests/test_live_perception.py
python scripts/dev_check.py
mneme --db /tmp/mneme-stage5-cli.sqlite3 run --json --tts-command "printf {text}" --voice soft --input "hello Mneme"
```

The focused Stage 5/runtime tests passed during implementation. Final full validation is recorded in the assistant completion summary for the commit that added this entry.
