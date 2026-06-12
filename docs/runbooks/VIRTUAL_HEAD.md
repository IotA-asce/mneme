# Stage 3 Virtual Head Runbook

Stage 3 adds a local terminal virtual head. It runs the existing deterministic cognition stack in one process and uses typed input instead of real camera or microphone input.

No real sensors, speakers, actuators, ROS nodes, GPIO, serial devices, or hardware libraries are used in this stage.

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

Stage 3 ships a deterministic fake backend. By default it reports:

- one fake camera,
- one fake microphone,
- one fake speaker.

Use this to test no-device behavior:

```bash
mneme run --no-fake-devices --json --input "hello"
```

Real platform discovery belongs to Stage 4.

## Verification

Run:

```bash
python scripts/dev_check.py
```

Stage 3 focused coverage is in:

```bash
python -m pytest tests/test_stage3_runtime.py
```
