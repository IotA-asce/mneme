# Local Cognitive Models Runbook

Status: M7.1 local Ollama adapter
Date: 2026-06-13

Mneme can now check a local Ollama chat model without making that model own the dialogue loop. This is the first safe step toward model-backed cognition: verify the service, verify the model, run one bounded probe, and return structured status.

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

## What This Does Not Do Yet

- It does not replace the deterministic dialogue planner.
- It does not connect the model to `mneme ui` chat responses.
- It does not let the model write confirmed memories.
- It does not send model output to skills or hardware.

The next cognition milestone is a bounded context builder and model dialogue realizer behind the existing dialogue contract.

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
