# Testing

Validation run:

- `.venv/bin/python -m pytest tests/test_model_runtime.py tests/test_stage6_local_living_lab.py` — 29 passed.
- `git diff --check` — passed.
- `.venv/bin/python scripts/dev_check.py` — database init, memory smoke, and 235 pytest tests passed.
- `.venv/bin/mneme models list --profile local-cognition --json` — listed the service-managed `qwen2_5_1_5b_ollama` entry.
- `.venv/bin/mneme models verify qwen2_5_1_5b_ollama --json` — returned `service_managed_use_backend_check`.
- `.venv/bin/mneme cognition check --no-probe --json` — reached Ollama but returned `model_missing` because `qwen2.5:1.5b` is not installed yet.

Manual local check after model pull remains:

```bash
ollama pull qwen2.5:1.5b
mneme cognition check --json
```
