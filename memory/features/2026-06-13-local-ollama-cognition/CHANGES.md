# Changes

- Added `model_runtime.py` with structured model messages, requests, responses, list results, checks, a fake runtime, and an Ollama runtime.
- Added `mneme cognition check` with JSON output, no-probe mode, timeout configuration, base URL override, and missing-model guidance.
- Added the service-managed `qwen2_5_1_5b_ollama` registry entry for `qwen2.5:1.5b`.
- Extended model registry records to distinguish file-managed and service-managed models.
- Added fake-backed tests for adapter behavior and CLI JSON output.
- Added local cognitive model documentation and updated README/status/backlog.
