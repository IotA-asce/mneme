# Local Cognitive Models Runbook

Status: M7.2-M7.4 local model-backed wording
Date: 2026-06-13

Mneme can now check a local Ollama chat model and use it as an optional wording layer after deterministic memory retrieval, executive intent, and dialogue planning. The model does not own memory selection, safety, intent, or durable writes.

The default first model is `qwen2.5:1.5b`.

## Install Ollama And Model

Ollama must be installed and running on the host.

Check the service manually:

```bash
ollama --version
ollama list
```

Install the default local cognitive model:

```bash
ollama pull qwen2.5:1.5b
```

Mneme does not auto-download this model. Pulling models is an explicit host-level action.

## Mneme Check

Check Ollama and run a small non-streaming probe:

```bash
mneme cognition check --json
```

Check only service/model availability without generating text:

```bash
mneme cognition check --no-probe --json
```

Use a custom Ollama URL or model:

```bash
mneme cognition check --base-url http://localhost:11434 --model qwen2.5:1.5b --json
```

When the model is missing, the command returns a structured `model_missing` result and suggests:

```bash
ollama pull qwen2.5:1.5b
```

The command exits with status `0` when the check is healthy and status `1` when the backend or model is not ready.

## Local Model Wording

Use local model wording in terminal mode:

```bash
mneme run --profile local-cognition --json --input "hello Mneme"
```

Use local cognition with the broader local-lab profile:

```bash
mneme run \
  --profile local-lab \
  --cognition-backend ollama \
  --cognition-model qwen2.5:1.5b \
  --json
```

Open the browser UI with local cognition enabled:

```bash
mneme ui --cognition-profile local
```

The runtime snapshot includes:

- whether local cognition is enabled,
- backend and model name,
- last model latency,
- whether the last response was model-realized or deterministic fallback,
- memory refs used by the final response,
- fallback reason when validation fails.

## Safety Boundary

The local model receives a bounded `CognitiveContextPacket` containing the user utterance, working memory, attention, safety/avatar state, and allowed retrieved memories.

Rules enforced before model output is spoken:

- `never_say` and `internal_only` memories are excluded.
- `restricted` memories become `restricted memory exists` unless trusted internal mode is used.
- model output must be structured JSON,
- model output may use only memory refs present in the context packet,
- model output must not claim inferred facts were user-confirmed,
- low-confidence memory use is hedged,
- failures fall back to deterministic dialogue text.

## What This Does Not Do Yet

- It does not replace the deterministic dialogue planner.
- It does not let the model write confirmed memories.
- It does not send model output to skills or hardware.
- It does not add multi-step reasoning, planning, embeddings, or cloud models.

The next cognition layer now has a foundation in `docs/runbooks/COGNITIVE_BENCHMARKS.md`: fixture-based cognitive benchmarks, conservative capability ladder evidence, turn classification, and memory-backed explanation. The benchmark suite is still small and should be expanded before making broader capability claims.

## Failure Modes

- `server_unavailable`: Ollama is not running or not reachable at `--base-url`.
- `model_missing`: the service is reachable, but the requested model is not installed.
- `timeout`: the service or model did not respond before `--timeout-ms`.
- `malformed_response`: Ollama returned JSON that did not match the expected `/api/tags` or `/api/chat` shape.
- `http_error`: Ollama returned a non-success HTTP response.

## Rules

- Keep local cognition optional and local-first.
- Use fake model runtimes in automated tests.
- Treat model-generated memories as `model_inferred` unless the user confirms them.
- Do not let a model bypass retrieval, executive intent, skills, or safety.
- Do not add cloud dependency as a hard requirement.
