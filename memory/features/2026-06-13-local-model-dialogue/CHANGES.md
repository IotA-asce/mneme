# Changes

- Added `cognitive_context.py` for bounded, speakability-filtered prompt context.
- Added `model_dialogue.py` for structured model response realization and deterministic fallback.
- Extended `ModelRequest` with Ollama `format` support for structured output.
- Added optional `MnemeRuntime` model realizer injection and cognition snapshot status.
- Added `mneme run --profile local-cognition` and explicit cognition flags.
- Added `mneme ui --cognition-profile local` plus UI model status, latency, fallback, and memory-ref display.
- Added fake-backed tests for context filtering, model validation, runtime wiring, CLI wiring, and UI rendering.
- Updated README, runbook, repo status, backlog, implementation plan, and project memory.
