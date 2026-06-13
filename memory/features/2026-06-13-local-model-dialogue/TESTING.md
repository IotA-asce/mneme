# Testing

Validation run:

- `.venv/bin/python -m pytest tests/test_cognitive_context.py tests/test_model_dialogue.py tests/test_model_runtime.py tests/test_stage3_runtime.py tests/test_stage6_local_living_lab.py` — 48 passed.
- `git diff --check` — passed.
- `.venv/bin/python scripts/dev_check.py` — database init, memory smoke, and 248 pytest tests passed.
- `.venv/bin/mneme cognition check --json` — local Ollama and `qwen2.5:1.5b` passed.
- `.venv/bin/mneme run --profile local-cognition --device-backend none --json --input "hello Mneme"` — produced model-realized wording with no fallback.
- Temporary database two-turn smoke with `remember that I like green tea` then `what do I like?` — retrieved a memory ref and produced model-realized wording without treating the inferred fact as user-confirmed.

Manual local acceptance:

```bash
mneme cognition check --json
mneme run --profile local-cognition --json --input "hello Mneme"
mneme run --profile local-cognition --json --input "what do I like?"
mneme ui --cognition-profile local
```
