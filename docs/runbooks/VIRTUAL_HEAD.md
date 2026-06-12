# Stage 3 Virtual Head Runbook

Stage 3 adds a local terminal virtual head. It runs the existing deterministic cognition stack in one process and uses typed input instead of real camera or microphone input.

Stage 4 adds optional live perception command adapters. Stage 5 adds virtual speech output, avatar state, virtual skills, and barge-in handling. No physical actuators, ROS nodes, GPIO, serial devices, or hardware libraries are used by the virtual-head runtime.

## Setup

Install the package in editable mode:

```bash
python -m pip install -e '.[dev]'
```

Initialize the local database:

```bash
mneme-memory init-db
```

## Scripted Run

Use scripted input for deterministic demos and tests:

```bash
mneme run --input "hello Mneme"
```

JSON output is available for replay/debug use:

```bash
mneme run --json --input "remember that I like tea" --input "what do I like"
```

The first line becomes a typed `speech_transcript` perception event and an explicit memory candidate. The second line can retrieve the stored fact and produce a dialogue plan.

## Interactive Run

Run without `--input` to read from standard input:

```bash
mneme run
```

Type `/quit` or `/exit` to stop.

## What Gets Wired

`MnemeRuntime` constructs and wires:

- local event bus,
- `MnemeMemory`,
- sensory echo,
- working memory,
- world model,
- context windows,
- attention manager,
- memory promoter,
- fact extractor,
- consolidation daemon,
- executive,
- dialogue planner,
- fake peripheral discovery.

## Peripheral Discovery

The deterministic fake backend remains the default. By default it reports:

- one fake camera,
- one fake microphone,
- one fake speaker.

Use this to test no-device behavior:

```bash
mneme run --no-fake-devices --json --input "hello"
```

Stage 4 adds an opt-in real inventory backend:

```bash
mneme run --device-backend real --json --input "hello"
```

Real discovery lists host devices only. It does not open camera streams, record microphone audio, play audio, or run perception models. See `docs/runbooks/REAL_DEVICE_DISCOVERY.md`.

Stage 4 live-perception workers can be enabled with local command adapters:

```bash
mneme run --device-backend real --camera-command "your-camera-tool --output {output}" --json
mneme run --device-backend real --speech-command "your-local-asr --device {device_id}" --json
```

See `docs/runbooks/LIVE_PERCEPTION.md` for command contracts, retention controls, and limitations.

## Conversational Presence

Stage 5 virtual presence is enabled by default. Dialogue plans become virtual speech skill goals, and the JSON snapshot exposes avatar state plus virtual skill status:

```bash
mneme run --json --virtual-speech-duration-ms 500 --input "hello Mneme"
```

Use a local TTS command already installed on the host:

```bash
mneme run --tts-command "say {text}" --voice Samantha --input "hello Mneme"
```

Disable virtual presence when only text responses are needed:

```bash
mneme run --no-virtual-presence --input "hello Mneme"
```

See `docs/runbooks/CONVERSATIONAL_PRESENCE.md` for voice persistence, local TTS placeholders, and barge-in behavior.

## Verification

Run:

```bash
python scripts/dev_check.py
```

Stage 3 focused coverage is in:

```bash
python -m pytest tests/test_stage3_runtime.py
```

Stage 5 focused coverage is in:

```bash
python -m pytest tests/test_conversational_presence.py
```
