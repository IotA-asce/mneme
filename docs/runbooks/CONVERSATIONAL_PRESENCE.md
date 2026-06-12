# Conversational Presence Runbook

Stage 5 adds a virtual presence layer to the local Mneme runtime. It turns dialogue plans into virtual skill goals, records simulated speech output, optionally calls a local TTS command, and maintains a JSON-friendly avatar state for demos and debugging.

No physical actuators, GPIO, serial devices, ROS nodes, or hardware libraries are used in this stage.

## Setup

Install the package and initialize the local database:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
mneme-memory init-db
```

Run the project check:

```bash
python scripts/dev_check.py
```

## Simulated Speech

The default speech backend is simulated. It records spoken text in the runtime JSON output but does not play audio:

```bash
mneme run --json --virtual-speech-duration-ms 500 --input "hello Mneme"
```

Relevant JSON appears under:

```text
result.snapshot.presence
result.snapshot.presence.avatar
result.snapshot.presence.skills.outputs
```

The avatar state reports `idle`, `listening`, `thinking`, `speaking`, or `safety`, plus gaze target, blink pattern, mouth state, and the latest virtual skill status.

## Local TTS Adapter

Use `--tts-command` to call a speech command already installed on the host. Mneme substitutes only these placeholders:

- `{text}`: the utterance text,
- `{voice}`: the selected voice label,
- `{device_id}`: reserved for a speaker device ID.

Example with macOS `say`:

```bash
mneme run --tts-command "say {text}" --input "hello Mneme"
```

Example using a voice label:

```bash
mneme run --tts-command "say -v {voice} {text}" --voice Samantha --input "hello Mneme"
```

The base package does not bundle a TTS engine. If the command exits non-zero or times out, the virtual speech skill publishes a failed status instead of crashing the architecture.

## Voice Persistence

`--voice` persists the selected label as procedural memory under the `speech` skill:

```bash
mneme run --voice Samantha --input "hello Mneme"
```

Later runs without `--voice` reuse the stored voice. Passing a different `--voice` creates a new procedural parameter version and supersedes the previous one.

## Barge-In

If user speech arrives while a virtual speech goal is active, the coordinator preempts the active speech goal and increments the `barge_ins` counter:

```bash
mneme run \
  --json \
  --virtual-speech-duration-ms 5000 \
  --input "hello Mneme" \
  --input "wait, one more thing"
```

This is a deterministic simulation of turn interruption. Real endpointing quality still depends on the Stage 4 speech adapter.

## Disable Presence

Use this when you only want text utterances and cognition state:

```bash
mneme run --no-virtual-presence --input "hello Mneme"
```

## Verification

Focused Stage 5 tests:

```bash
python -m pytest tests/test_conversational_presence.py
```

Runtime regression tests:

```bash
python -m pytest tests/test_conversational_presence.py tests/test_stage3_runtime.py tests/test_live_perception.py
```

Full project check:

```bash
python scripts/dev_check.py
```

## Boundaries

Stage 5 owns virtual expression and local speech output only. It must not:

- command physical motors,
- open or configure hardware directly,
- bypass executive intent,
- let TTS command failures crash the runtime,
- treat simulated speech completion as proof of physical safety.
