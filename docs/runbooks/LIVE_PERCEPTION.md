# Live Perception Runbook

Stage 4 adds live-perception worker contracts for camera frames and speech transcripts. The runtime can use local command adapters to capture frames or produce transcripts without adding OpenCV, audio, or ASR dependencies to the base install.

Fake and scripted backends remain the deterministic path for tests and CI.

## Boundary

Live perception workers may:

- select devices from the discovery snapshot,
- run configured local capture/transcription commands,
- publish standard `perception_observation` events,
- store raw frame/transcript traces with provenance,
- create memory candidates for important observations,
- enforce bounded frame archive retention.

They must not:

- call cloud ASR by default,
- bypass the event bus,
- command skills or actuators,
- store unbounded video,
- silently ignore provenance or confidence.

## Camera Frames

Use `--camera-command` with a command that writes one image to `{output}`:

```bash
mneme run \
  --device-backend real \
  --camera-command "your-camera-tool --output {output}" \
  --json \
  --input "hello"
```

Available placeholders:

- `{output}`: archive path for the frame file,
- `{device_id}`: Mneme device ID,
- `{label}`: OS-reported device label.

The command may print JSON with detections:

```json
{
  "detections": [
    {
      "person_id": "alice",
      "label": "Alice",
      "confidence": 0.91
    }
  ]
}
```

It may also write a sidecar file next to the frame, named like `frame.jpg.json`, with the same structure. Detections become `person_seen` observations compatible with the simulated worker.

## Speech Transcripts

Use `--speech-command` with a local command that prints transcript text or JSON:

```bash
mneme run \
  --device-backend real \
  --speech-command "your-local-asr --device {device_id}" \
  --json
```

Plain text stdout becomes the transcript. JSON stdout may include:

```json
{
  "speaker": "alice",
  "transcript": "remember that I like green tea",
  "confidence": 0.86,
  "duration_ms": 1200
}
```

Speech events publish `speech_transcript` observations, store transcript raw traces, and create memory candidates. Explicit "remember" phrases are tagged for semantic extraction using the same deterministic parser as typed input.

## Retention

Frame archive settings:

```bash
mneme run \
  --camera-command "your-camera-tool --output {output}" \
  --frame-archive-dir .local/perception_frames \
  --max-archived-frames 1000 \
  --max-frame-archive-bytes 536870912 \
  --max-frame-age-ms 604800000
```

The archive prunes old frame files by age, count, and total byte size. Transcript raw traces are stored in SQLite and monitored through lifecycle events; destructive transcript deletion remains an explicit future retention/purge policy, not an automatic side effect of live capture.

## Fusion

`PerceptionFusionCalibrator` watches `person_seen` and `speech_transcript` observations. If a recent person observation matches the speaker, it publishes a `world_state_update` with `state_key=perception_fusion` and latency/confidence details.

## Verification

Run focused tests:

```bash
python -m pytest tests/test_live_perception.py tests/test_real_peripherals.py tests/test_stage3_runtime.py
```

Run the full project check:

```bash
python scripts/dev_check.py
```

## Limitations

- The base package does not include a native camera library, face model, VAD, or ASR engine.
- Real capture depends on the configured local command and the host's permissions.
- Face/person detection is accepted from command JSON or sidecar metadata; Mneme does not yet ship a built-in detector.
- Continuous video and continuous raw audio are intentionally not stored.
