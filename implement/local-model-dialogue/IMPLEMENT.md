# Local Model Dialogue — Implementation Plan

Date: 2026-06-13
Status: Implemented

## Phases

1. Cognitive context builder
   - Add a JSON-friendly context packet from user utterance, intent, working memory, attention, safety, avatar state, retrieval bundle, ranking explanations, and provenance.
   - Enforce speakability filtering and deterministic character budgets.

2. Model dialogue realizer
   - Add a realizer that calls the model after deterministic dialogue planning.
   - Request structured JSON output through the existing model runtime adapter.
   - Validate memory refs, response length, source-type wording, and withheld-memory safety.
   - Fall back to deterministic text on any failure.

3. Runtime and UI integration
   - Add optional `MnemeRuntime` model realizer injection.
   - Add `mneme run --profile local-cognition`.
   - Add `mneme ui --cognition-profile local`.
   - Expose cognition status and last realization metadata in snapshots and UI.

4. Docs and memory
   - Update runbooks, README, repo status, backlog, implementation notes, and durable memory.

## Validation

- Focused tests for context, model dialogue, model runtime, runtime integration, and UI rendering.
- Full developer check.
- Manual local acceptance with `qwen2.5:1.5b`.

## Rollback

Remove the context/realizer modules, revert the runtime optional injection, remove CLI/UI cognition flags, and restore docs/backlog/memory status to M7.1-only local model readiness.

## Definition of Done

- Deterministic default runtime behavior is unchanged.
- Local cognition is opt-in.
- Model output never invents memory refs or confirmed status.
- UI/JSON surfaces whether a response used the model or fallback.
- Tests do not require Ollama.
