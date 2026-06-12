# Scenario Replay Runbook

Status: V1 local deterministic replay  
Date: 2026-06-12

Scenario replay feeds deterministic simulated perception events through Mneme's local runtime bus. It is intended for tests, demos, and future replay tooling before real sensors or ROS 2 are introduced.

It does not use cameras, microphones, OpenCV, Whisper, audio libraries, GPIO, serial devices, motors, or robot hardware.

## Entry Point

Run a scenario fixture:

```bash
python scripts/replay_scenario.py tests/fixtures/basic_conversation.yaml
```

The command prints JSON containing:

- replayed runtime events,
- memory candidates emitted by important steps,
- sensory echo contents,
- working-memory snapshot.

## Python API

```python
from android_brain_memory import EventBus, ScenarioReplayRunner

bus = EventBus(clock=lambda: 1000)
result = ScenarioReplayRunner(bus).replay_file("tests/fixtures/basic_conversation.yaml")
```

Attach sensory echo and working memory before replay:

```python
from android_brain_memory import SensoryEchoBuffer, WorkingMemory

echo = SensoryEchoBuffer()
working = WorkingMemory()
echo.attach_to_bus(bus)
working.attach_to_bus(bus)
```

## Scenario Format

Scenarios may be YAML or JSON. The top-level shape is:

```yaml
name: basic_conversation
start_ts: 1000
default_ttl_ms: 5000
steps:
  - id: user_speech
    at_ms: 20
    worker: speech_transcript
    confidence: 0.96
    important: true
    payload:
      speaker: user
      transcript: "Mneme, remember that I prefer short calibration prompts."
      topic: calibration
```

Fields:

- `name`: scenario name.
- `start_ts`: base timestamp in milliseconds.
- `default_ttl_ms`: default TTL for events that do not specify one.
- `steps`: ordered list of simulated worker events.

Step fields:

- `id`: deterministic step identifier. Runtime event IDs use `evt_<id>`.
- `at_ms`: offset from `start_ts`.
- `worker`: simulated worker name.
- `confidence`: probability from `0.0` to `1.0`.
- `ttl_ms`: optional event TTL override.
- `source`: optional source override.
- `payload`: JSON-friendly event payload.
- `important`: when true, replay emits a memory candidate event.
- `memory_candidate`: optional explicit `MemoryCandidate` payload.

## Simulated Workers

Supported worker names:

- `face_person`
- `speech_transcript`
- `sound_direction`
- `touch`
- `body_health`

Aliases:

- `person`
- `speech`
- `sound`
- `health`

### Face/Person

```yaml
worker: face_person
payload:
  person_id: user
  label: User
  expression: attentive
```

Publishes a `perception_observation` with `observation_type: person_seen`.

### Speech Transcript

```yaml
worker: speech_transcript
payload:
  speaker: user
  transcript: "Hello Mneme"
  topic: greeting
```

Publishes a `perception_observation` with `observation_type: speech_transcript`. Working memory can use this to update current speaker, topic, and recent dialogue turns.

### Sound Direction

```yaml
worker: sound_direction
payload:
  direction_deg: 15
  source_label: user
```

Publishes a `perception_observation` with `observation_type: sound_direction`.

### Touch

```yaml
worker: touch
payload:
  zone: left_cheek
  gesture: tap
```

Publishes a `perception_observation` with `observation_type: touch`.

### Body/Internal Health

```yaml
worker: body_health
payload:
  status: nominal
  battery_pct: 87
  safety_level: normal
```

Publishes a `perception_observation` with `observation_type: body_health`. If `safety_level` is present, replay also publishes a `safety_event` so working memory can update safety context.

## Memory Candidates

Important events can become memory candidates.

The simplest option:

```yaml
important: true
```

This creates a deterministic candidate from the event payload.

For explicit control, provide `memory_candidate`:

```yaml
memory_candidate:
  candidate_id: cand_user_short_calibration_prompts
  candidate_type: user_preference_observation
  summary: "User prefers short calibration prompts."
  source_type: sensor_observed
  confidence: 0.96
  features:
    novelty: 0.7
    task_relevance: 0.9
    social_relevance: 0.8
    surprise: 0.2
    risk: 0.0
    contradiction: 0.0
    repetition_signal: 0.1
    explicit_remember_flag: 1.0
  entities:
    - user
  tags:
    - preference
    - calibration
```

Replay emits the candidate as a `memory_candidate` runtime event. It does not automatically write facts, episodes, or raw traces.

## Boundaries

- Simulated workers publish observations only.
- Replay does not infer facts from arbitrary text.
- Replay does not command skills or actuators.
- Replay does not run real sensors.
- Replay does not imply safety certification.

## Tests

Targeted tests:

```bash
python -m pytest tests/test_scenario_replay.py
```

The basic fixture is:

```text
tests/fixtures/basic_conversation.yaml
```
