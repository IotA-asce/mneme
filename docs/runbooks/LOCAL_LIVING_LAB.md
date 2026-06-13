# Local Living Lab Runbook

Status: Stage 6 foundation with M9.1 fake-backed speech hardening
Date: 2026-06-14

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

For continuous microphone polling, add `--live` or use a bounded smoke run:

```bash
mneme run --profile local-speech --live --json
mneme run --profile local-speech --live-ticks 5 --json
```

Useful flags:

```bash
mneme run \
  --profile local-speech \
  --asr-model .local/models/faster-whisper-base \
  --asr-device cpu \
  --asr-compute-type int8 \
  --live \
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

Runtime JSON includes a `speech_loop` snapshot for speech reliability:

- latest speech worker report (`transcribed`, `no_speech`, `no_microphone`, `capture_error`),
- ASR, response, and TTS latency fields when available,
- duplicate-response suppression count,
- barge-in count,
- TTS completion/failure/preemption counts,
- stuck-state count and latest failure reason.

Run the fake-backed speech soak suite before manual device testing:

```bash
mneme eval speech --json
```

Run one fixture while debugging:

```bash
mneme eval speech --fixture tests/fixtures/speech/barge_in.yaml --json
```

The soak suite uses fake speech/TTS backends and does not require real devices, ASR models, or speakers.

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

The UI inventories devices at startup without opening sensors. If a dropdown only
shows **Auto**, grant the relevant camera/microphone permission if macOS asks,
connect the device, then press **Refresh list**. Refreshing rescans host devices
without restarting the UI.

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

The UI's default real-device scan timeout is longer than the terminal default so
macOS `system_profiler` has time to return camera/audio inventory. It still does
not open the camera, record audio, or play audio during discovery.

## Evaluation Logs

Record local daily-driver metrics:

```bash
mneme run --json --input "hello Mneme" --evaluation-log .local/evaluation/daily_driver.jsonl
```

Summarize:

```bash
mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json
```

Current metrics cover response generation, memory recall signal, skill status count, safety event count, speech-loop state, ASR/response/TTS latency fields, no-speech count, capture error count, TTS failure count, duplicate suppression count, barge-in count, and stuck-state count. Future work should add private-log redaction, replay from real local runs, latency histograms, correction rate, contradiction rate, repeated-visitor continuity, and bounded procedural adaptation.

## Manual Local Speech Acceptance

After optional dependencies and local model files are available, manually validate:

```bash
mneme run \
  --profile local-speech \
  --asr-model .local/models/faster-whisper-base \
  --tts-command "say {text}" \
  --evaluation-log .local/evaluation/daily_driver.jsonl \
  --json
```

Check:

- microphone permission is granted,
- ASR returns a transcript with bounded latency,
- no speech produces `no_speech` instead of a response,
- TTS playback succeeds or reports a structured failure,
- speaking over Mneme increments `barge_ins`,
- repeated live transcripts inside the duplicate window do not create duplicate spoken replies,
- `mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json` shows the expected speech metrics.

## Safety Boundaries

- No motors, GPIO, serial, PWM, firmware flashing, ROS control, or physical actuator commands are involved.
- Local media backends publish observations only.
- Dialogue produces virtual speech goals; TTS publishes skill status.
- Hardware embodiment remains deferred to Stage 8.
