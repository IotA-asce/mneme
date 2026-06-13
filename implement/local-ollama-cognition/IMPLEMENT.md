# Local Ollama Cognition Adapter — Implementation Plan

Date: 2026-06-13
Status: Implemented

## Phases

1. Add model runtime contracts
   - Add request, message, response, model-list, and health-check dataclasses.
   - Add fake runtime for tests.
   - Add Ollama runtime using `/api/tags` and non-streaming `/api/chat`.

2. Add CLI entry point
   - Add `mneme cognition check`.
   - Support `--backend ollama`, `--base-url`, `--model`, `--timeout-ms`, `--no-probe`, and `--json`.
   - Return structured failures for unavailable server, missing model, timeout, HTTP error, and malformed JSON.

3. Update model registry
   - Add service-managed model metadata for `qwen2.5:1.5b`.
   - Keep file-managed verification behavior for `.local/models/`.

4. Documentation and memory
   - Add local cognitive model runbook.
   - Update README, repo status, backlog, and project memory.

## Validation

- Unit tests for fake runtime and Ollama request/response parsing.
- CLI JSON tests with an injected fake adapter.
- Stage 6 registry test for service-managed Ollama metadata.
- Full developer check.

## Rollback

Remove `model_runtime.py`, the `mneme cognition` CLI branch, the Ollama registry record, and the related docs/backlog/memory entries.

## Definition of Done

- Ollama checks work without adding dependencies.
- CI does not require Ollama or downloaded models.
- Missing-model output clearly suggests `ollama pull qwen2.5:1.5b`.
- Runtime dialogue remains deterministic.
