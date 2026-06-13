# Local Model Dialogue

## Problem

Mneme could verify Ollama readiness, but the runtime still used only deterministic response text. The project needs local model-backed wording without letting the model own intent, memory, safety, or persistence.

## Desired Outcome

Add a bounded cognitive context packet, a model dialogue realizer with schema validation and deterministic fallback, and runtime/UI controls for opt-in local cognition.

## User Value

The local brain can start feeling less canned while remaining auditable: responses can be worded by a local model, but memory refs, provenance, and fallback state remain visible.

## Affected Systems

- runtime dialogue path,
- local model runtime requests,
- local browser UI snapshot,
- virtual-head CLI,
- documentation, backlog, and project memory.

## Assumptions

- Default model remains `qwen2.5:1.5b`.
- Ollama is optional and local.
- Fake model runtimes cover automated tests.

## Constraints

- No cloud dependency.
- No new Python dependency.
- No model-to-actuator path.
- No model-confirmed facts.
- Deterministic fallback must always remain available.

## Non-Goals

- Multi-step reasoning or planning.
- Embeddings or vector search.
- Autonomous memory writes from model output.
- Physical hardware integration.
