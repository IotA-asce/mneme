# Local Living Lab Runbook

Status: Stage 6 foundation
Date: 2026-06-13

The Local Living Lab is Mneme's brain-first path: run the cognition loop on the current computer with local microphone, speaker, camera, local models, memory, attention, dialogue, virtual presence, and evaluation logs. It does not control physical robot hardware.

## Install

Base development install:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

Optional local media/model install:

```bash
python -m pip install -e '.[local-lab]'
```

Use narrower extras when debugging one area:

```bash
python -m pip install -e '.[local-speech]'
python -m pip install -e '.[vision-local]'
```

## Model Check

Model files live under `.local/models/` and are not committed.

```bash
mneme models list --json
mneme models verify --json
```

If a model is missing, place the compatible local files at the path shown by `verify`. Downloads are disabled unless a registry entry explicitly documents a source URL.

## Local Speech Loop

Run the native speech profile after installing optional dependencies and placing the ASR/TTS model files:

```bash
mneme run --profile local-speech --json
```

Useful flags:

```bash
mneme run \
  --profile local-speech \
  --asr-model .local/models/faster-whisper-base \
  --asr-device cpu \
  --asr-compute-type int8 \
  --record-ms 3000 \
  --json
```

Expected flow:

1. microphone capture writes a bounded local WAV segment,
2. faster-whisper produces a `speech_transcript` observation,
3. memory/attention/executive/dialogue process the transcript,
4. dialogue creates a virtual `speech` skill goal,
5. TTS or the simulated speech backend publishes skill status.

Failure should be explicit. Missing optional packages, missing model files, microphone permission failures, empty speech, slow ASR, and TTS errors should surface as failed observations/status rather than silent success.

## Local Vision Loop

Run native vision after installing optional dependencies and granting camera permission:

```bash
mneme run --profile local-vision --face-backend mediapipe --json
```

The first native vision target is reliable observation, not identity recognition:

- `camera_frame`,
- `person_seen`,
- bounding box / keypoint metadata,
- attention-facing signal,
- anonymous session person IDs.

Do not treat expression or emotion-like cues as truth. Do not add face embeddings or unrestricted recognition until a specific model/license decision is approved.

## Browser UI

Start the lightweight local UI:

```bash
mneme ui
```

Open `http://127.0.0.1:8765`.

The UI visualizes runtime snapshot state and sends typed input. It does not own cognition, memory, attention, executive intent, or skills.

The UI also has device selectors for:

- camera,
- microphone,
- speaker.

Press **Save devices** after selecting devices. The selection is saved in:

```text
.local/runtime_preferences.json
```

Future `mneme ui` and `mneme run` sessions load this file automatically. Terminal runs can temporarily override saved devices:

```bash
mneme run \
  --profile local-speech \
  --microphone-device-id <device-id> \
  --speaker-device-id <device-id> \
  --json
```

Use the device IDs shown in the UI runtime JSON or `/state` endpoint. If a saved device is unavailable, Mneme falls back to the first available device of that kind.

## Evaluation Logs

Record local daily-driver metrics:

```bash
mneme run --json --input "hello Mneme" --evaluation-log .local/evaluation/daily_driver.jsonl
```

Summarize:

```bash
mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json
```

Current metrics cover response generation, memory recall signal, skill status count, safety event count, and barge-in count. Future Stage 7 work should add redaction, soak replay, latency histograms, correction rate, contradiction rate, repeated-visitor continuity, and stuck-state counts.

## Safety Boundaries

- No motors, GPIO, serial, PWM, firmware flashing, ROS control, or physical actuator commands are involved.
- Local media backends publish observations only.
- Dialogue produces virtual speech goals; TTS publishes skill status.
- Hardware embodiment remains deferred to Stage 8.
