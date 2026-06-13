# Local Ollama Cognition Adapter

## Problem

Mneme has a deterministic cognition stack and local model hygiene, but no safe way to verify that a local chat model runtime is installed, reachable, and ready before later model-backed cognition work.

## Desired Outcome

Add a small local model runtime layer that can check Ollama, verify the selected model, run one bounded probe, and return structured status without changing dialogue behavior.

## User Value

The user can prepare the brain-first local lab for model-backed cognition while keeping the current memory, attention, dialogue, skill, and safety boundaries intact.

## Affected Systems

- local model registry,
- virtual-head CLI,
- future cognition/model integration,
- documentation and project memory.

## Constraints

- Use standard-library HTTP only.
- Do not add a Python Ollama dependency.
- Do not auto-download models.
- Do not wire model output into runtime dialogue yet.
- Keep tests fake-backed and CI-safe.

## Non-Goals

- Model-backed UI or terminal responses.
- Cognitive context construction.
- Memory writes from model output.
- Cloud LLM support.
- Hardware or actuator integration.
