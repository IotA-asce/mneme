# Mneme

Mneme is a memory-centered cognition engine for a lifelike android head.

The current repository is a local Python prototype for the **brain-first Local Living Lab** phase of that architecture. It focuses on safe, testable cognition boundaries: perception workers publish observations, state builders publish state, memory stores and retrieves context, attention chooses what matters, the executive publishes intent, virtual skills consume that intent, and physical actuators remain outside the runtime.

Mneme does not currently control physical hardware.

## Current Status

As of 2026-06-13, Stages 0-5 of the master roadmap are complete and Stage 6 has its foundation implemented:

- **Stage 0:** V1 memory core.
- **Stage 1:** autonomous memory lifecycle.
- **Stage 2:** bench cognition integration.
- **Stage 3:** cross-platform runtime and terminal virtual head.
- **Stage 4:** real device discovery and live-perception worker contracts.
- **Stage 5:** conversational presence with virtual speech, avatar state, virtual skills, and interruption handling.
- **Stage 6:** Local Living Lab foundation with optional native local speech, model registry, native camera/person-presence backends, a local browser UI, and evaluation logs.

Physical embodiment is now deferred behind the Local Living Lab. ROS, GPIO, serial, PWM, servo control, microcontroller flashing, and physical actuator work are not part of the current runtime.

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

### Local Living Lab

Stage 6 starts the brain-first local loop:

- Optional local extras are declared for microphone/speaker streaming, WebRTC VAD, faster-whisper ASR, Kokoro TTS, OpenCV camera capture, and MediaPipe face detection.
- Native local backends sit behind the existing worker/output contracts, so `speech_transcript`, virtual `speech` goals, skill statuses, memory, attention, executive, and dialogue flow stay unchanged.
- `config/models.yaml` tracks local model metadata; model files live under `.local/models/` and are never committed.
- `mneme models list`, `mneme models verify`, and guarded `mneme models download` support local model hygiene.
- `mneme run --profile local-speech` opts into native microphone/ASR/TTS backends when optional packages and local models are available.
- `mneme run --profile local-vision` opts into OpenCV camera capture and optional MediaPipe face/person observations.
- `mneme ui` serves a lightweight browser UI that visualizes avatar/runtime state, accepts typed input, refreshes the local device inventory, and saves preferred camera/microphone/speaker selections.
- `--evaluation-log` and `mneme eval summarize` record local daily-driver metrics for later brain-loop evaluation.

### Live Perception

Stage 4 live perception is implemented through repo-owned worker contracts and local command adapters:

- `LiveVisionWorker` selects a discovered camera, captures bounded keyframes through a configured command adapter, stores raw frame traces, and publishes `camera_frame` / `person_seen` events.
- `LiveSpeechWorker` selects a discovered microphone, accepts local transcript output through a configured command adapter, stores transcript traces, and publishes `speech_transcript` events.
- Explicit "remember" phrases in live transcripts can become memory candidates and semantic facts through the existing promotion/extraction pipeline.
- `PerceptionFusionCalibrator` publishes speaker/person match diagnostics with latency and confidence.
- Frame archive retention is bounded by count, age, and total bytes.

The base package intentionally does not install OpenCV, face models, VAD, ASR, or TTS engines by default. Native backends are optional extras and are tested with fakes in CI.

## What Is Not Implemented Yet

- Real local model files are not bundled. You must place or download compatible models under `.local/models/`.
- Real-device quality has not been tuned in CI; local mic/camera permissions, model speed, and audio playback must be validated on your machine.
- The browser UI is a lightweight local dashboard, not a polished graphical avatar renderer.
- Long-running process supervision and private-log redaction workflows are not implemented yet.
- Physical skill controllers and actuator bridge.
- Physical hardware control, GPIO, serial, PWM, firmware flashing, or ROS runtime nodes.
- Cloud LLM integration.

## Install

Mneme targets Python 3.11.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

Optional Local Living Lab extras:

```bash
# Microphone/speaker streaming
python -m pip install -e '.[audio-local]'

# WebRTC VAD
python -m pip install -e '.[vad-local]'

# faster-whisper ASR
python -m pip install -e '.[asr-local]'

# Kokoro TTS
python -m pip install -e '.[tts-local]'

# OpenCV + MediaPipe vision
python -m pip install -e '.[vision-local]'

# All current local speech/vision extras together
python -m pip install -e '.[local-lab]'
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

The current suite covers memory models, storage, migrations, salience, retrieval, provenance, conflicts, consolidation, decay, runtime events, working memory, scenario replay, world model, attention, executive behavior, dialogue planning, device discovery, live-perception adapters, conversational presence, Local Living Lab fake backends/model registry/UI/evaluation logging, and the virtual-head runtime.

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

## Local Living Lab

Inspect local model configuration:

```bash
mneme models list --json
mneme models verify --json
```

Model files belong under `.local/models/`. The default registry documents expected paths, license notes, and profiles, but does not download model files unless a registry entry explicitly includes a `download_url`.

Run native local speech when optional packages and models are installed:

```bash
python -m pip install -e '.[local-speech]'
mneme models list --profile local-speech --json
mneme models verify --json
mneme run --profile local-speech --json
```

Useful local speech flags:

```bash
mneme run \
  --profile local-speech \
  --asr-model .local/models/faster-whisper-base \
  --asr-device cpu \
  --asr-compute-type int8 \
  --record-ms 3000 \
  --json
```

Run native local vision when optional packages and a camera are available:

```bash
python -m pip install -e '.[vision-local]'
mneme run --profile local-vision --face-backend mediapipe --json
```

Open the local browser UI:

```bash
mneme ui
```

Then visit `http://127.0.0.1:8765`. The UI visualizes runtime/avatar state, can submit typed input, and can save preferred camera, microphone, and speaker devices. Use **Refresh list** if the dropdowns only show **Auto** after granting permissions or connecting a device. Saved device selections are stored in `.local/runtime_preferences.json` and are reused by later `mneme ui` and `mneme run` sessions.

Terminal runs can also use explicit one-off device IDs:

```bash
mneme run \
  --profile local-speech \
  --microphone-device-id microphone_abc123 \
  --speaker-device-id speaker_def456 \
  --json
```

Record and summarize local daily-driver metrics:

```bash
mneme run --json --input "hello Mneme" --evaluation-log .local/evaluation/daily_driver.jsonl
mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json
```

See `docs/runbooks/LOCAL_LIVING_LAB.md` and `docs/runbooks/LOCAL_MODELS.md`.

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
