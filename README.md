# Mneme

Mneme is a memory-centered cognition engine for a lifelike android head.

The current repository is a local Python prototype for the virtual-head phase of that architecture. It focuses on safe, testable cognition boundaries: perception workers publish observations, state builders publish state, memory stores and retrieves context, attention chooses what matters, the executive publishes intent, virtual skills consume that intent, and physical actuators remain outside the runtime.

Mneme does not currently control physical hardware.

## Current Status

As of 2026-06-13, Stages 0-5 of the master roadmap are implemented in the repo-owned architecture:

- **Stage 0:** V1 memory core.
- **Stage 1:** autonomous memory lifecycle.
- **Stage 2:** bench cognition integration.
- **Stage 3:** cross-platform runtime and terminal virtual head.
- **Stage 4:** real device discovery and live-perception worker contracts.
- **Stage 5:** conversational presence with virtual speech, avatar state, virtual skills, and interruption handling.

See `docs/architecture/MASTER_ROADMAP.md` and `docs/architecture/REPO_STATUS.md` for the detailed status record.

## What Works Now

### Memory Core

- SQLite storage with tracked, checksummed migrations.
- Dataclass domain models for candidates, salience, episodes, facts, queries, and bundles.
- Configurable salience scoring with explanations and explicit-remember override.
- Raw traces, episodes, facts, summaries, meta-memory, and working-context snapshots.
- Provenance chains across raw traces, episodes, facts, and summaries.
- Speakability filtering for memories that should not be spoken.
- Conflict-aware semantic facts: confirmed facts outrank inferred facts, and contradictions are not silently overwritten.
- Deterministic retrieval over facts, episodes, and summaries with ranking explanations.
- Decay/downranking, suppression, and explicit purge workflows.
- Deterministic consolidation summaries for repeated episodes.

### Runtime Cognition

- Local ROS-like event model and deterministic in-process event bus.
- Bounded sensory echo and explicit working memory.
- Scenario replay from YAML/JSON fixtures.
- Shared world model for persons, active speaker, sound, touch, internal state, and safety level.
- Attention manager with dwell/lock, habituation, inhibition-of-return, curiosity scanning, and ranking explanations.
- Executive intent generation with safety priority, goal stack, response timing, memory-informed responses, and deterministic idle rotation.
- Deterministic dialogue planner with provenance-aware phrasing and speakability filtering.
- Self model and versioned procedural-memory parameters.

### Virtual Head Runtime

- `mneme run` starts a one-process terminal virtual head.
- Typed input becomes `speech_transcript` perception events.
- Scripted JSON mode supports deterministic demos and replay/debug use.
- Fake camera, microphone, and speaker inventory is the default for tests and CI.
- Real OS-backed device inventory can list host cameras, microphones, and speakers.

### Conversational Presence

Stage 5 adds a virtual presence layer on top of the runtime:

- Dialogue plans become virtual `speech` skill goals.
- The default speech backend is simulated and records output in JSON without playing audio.
- Optional local TTS command adapters can play speech through tools installed on the host.
- Speech voice selection can be passed with `--voice` and is persisted as procedural memory.
- A virtual avatar state tracks listening, thinking, speaking, gaze target, idle blink pattern, and safety mode.
- Barge-in is handled deterministically: user speech while Mneme is speaking preempts the active speech skill.
- Virtual skills publish accepted/running/completed/preempted/canceled status events using the same event contracts future physical skills will use.

### Live Perception

Stage 4 live perception is implemented through repo-owned worker contracts and local command adapters:

- `LiveVisionWorker` selects a discovered camera, captures bounded keyframes through a configured command adapter, stores raw frame traces, and publishes `camera_frame` / `person_seen` events.
- `LiveSpeechWorker` selects a discovered microphone, accepts local transcript output through a configured command adapter, stores transcript traces, and publishes `speech_transcript` events.
- Explicit "remember" phrases in live transcripts can become memory candidates and semantic facts through the existing promotion/extraction pipeline.
- `PerceptionFusionCalibrator` publishes speaker/person match diagnostics with latency and confidence.
- Frame archive retention is bounded by count, age, and total bytes.

The base package intentionally does not bundle OpenCV, face models, VAD, or ASR engines. Those can be plugged in behind the command/backend contracts.

## What Is Not Implemented Yet

- Built-in native camera, face detection, VAD, or ASR backends.
- Built-in native TTS engine. Speech output is available only through a configured local command or the simulated backend.
- Graphical avatar rendering. The repo currently exposes virtual avatar state in JSON/terminal output.
- Physical skill controllers and actuator bridge.
- Physical hardware control, GPIO, serial, PWM, firmware flashing, or ROS runtime nodes.
- Cloud LLM integration.
- Full long-running daemon/process supervision.

## Install

Mneme targets Python 3.11.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

Initialize the local SQLite database:

```bash
mneme-memory init-db
```

The default database path is `.local/android_brain_memory.sqlite3`.

## Verify

Run the canonical local check:

```bash
python scripts/dev_check.py
```

This runs:

```bash
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
```

The current suite covers memory models, storage, migrations, salience, retrieval, provenance, conflicts, consolidation, decay, runtime events, working memory, scenario replay, world model, attention, executive behavior, dialogue planning, device discovery, live-perception adapters, conversational presence, and the virtual-head runtime.

## Memory CLI

Use the high-level CLI for JSON-oriented memory work:

```bash
mneme-memory inspect-db
mneme-memory retrieve --query-text memory --max-results 3
mneme-memory consolidate-once
```

Primary commands:

- `init-db`
- `remember-candidate`
- `add-episode`
- `add-fact`
- `retrieve`
- `consolidate-once`
- `inspect-db`
- `inspect-provenance`
- `inspect-decay`

The older script entry point remains available:

```bash
python scripts/mneme_memory.py inspect-db
```

See `docs/runbooks/MEMORY_CLI.md` for payload examples.

## Virtual Head

Run a typed terminal interaction:

```bash
mneme run --input "hello Mneme"
mneme run --json --input "remember that I like tea" --input "what do I like"
```

Run with simulated speech output visible in JSON:

```bash
mneme run --json --virtual-speech-duration-ms 500 --input "hello Mneme"
```

Use a local TTS command adapter. The base package does not install a TTS engine; the command must already exist on your machine.

```bash
mneme run --tts-command "say {text}" --voice Samantha --input "hello Mneme"
```

Command placeholders:

- `{text}`: utterance text from the dialogue planner,
- `{voice}`: selected voice label,
- `{device_id}`: optional speaker device ID.

Disable virtual presence if you only want text responses and cognition events:

```bash
mneme run --no-virtual-presence --input "hello Mneme"
```

Use real device inventory:

```bash
mneme run --device-backend real --json --input "hello"
```

Use an empty inventory for no-device tests:

```bash
mneme run --device-backend none --json --input "hello"
```

See `docs/runbooks/VIRTUAL_HEAD.md` and `docs/runbooks/CONVERSATIONAL_PRESENCE.md`.

## Live Perception Adapters

Camera frame command:

```bash
mneme run \
  --device-backend real \
  --camera-command "your-camera-tool --output {output}" \
  --json
```

Speech transcript command:

```bash
mneme run \
  --device-backend real \
  --speech-command "your-local-asr --device {device_id}" \
  --json
```

Available placeholders include:

- `{output}` for the frame archive path,
- `{device_id}` for the Mneme device ID,
- `{label}` for the OS-reported device label.

See `docs/runbooks/REAL_DEVICE_DISCOVERY.md` and `docs/runbooks/LIVE_PERCEPTION.md`.

## Scenario Replay

Run deterministic perception scenarios:

```bash
python scripts/replay_scenario.py tests/fixtures/basic_conversation.yaml
```

The script prints JSON containing the replay result, sensory echo snapshot, and working-memory snapshot.

See `docs/runbooks/SCENARIO_REPLAY.md`.

## Project Map

- `src/android_brain_memory/` - Python package.
- `storage/migrations/` - SQLite migrations.
- `config/memory.yaml` - salience, retention, privacy, and storage defaults.
- `interfaces/` - ROS-style draft contracts, aligned with Python models.
- `tests/` - unit, integration, storage, runtime, and replay tests.
- `docs/architecture/` - roadmap, status, runtime boundaries, serialization, and ROS plan.
- `docs/memory/` - memory model, storage, retrieval, salience, provenance, conflicts, consolidation, decay, and self model.
- `docs/runbooks/` - local development, CLI, virtual head, conversational presence, device discovery, live perception, and scenario replay.
- `memory/` - durable project memory for completed features, decisions, investigations, and risks.
- `implement/` - implementation plans and architectural rules for non-trivial changes.

## Safety Notes

- Mneme must remain debuggable and safe.
- Real hardware control is not present in this repository today.
- Perception workers publish observations only; they do not command behavior.
- Nothing should bypass the executive/skill/actuator separation when those layers are added.
- Do not store secrets, private credentials, or API tokens in memory provenance or repository files.

For contributor rules, read `AGENTS.md` before making changes.
