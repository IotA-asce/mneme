# Real Device Discovery Runbook

Stage 4 begins with host peripheral inventory. Mneme can now list cameras, microphones, and speakers discovered by the operating system.

This runbook is inventory only. The separate live-perception path can use configured local commands to capture frames or produce transcripts, but discovery by itself does not open camera streams, record microphone audio, run speech recognition, play speech, or verify permissions.

## Run

Install the package:

```bash
python -m pip install -e '.[dev]'
```

Run the virtual head with real device inventory:

```bash
mneme run --device-backend real --json --input "hello"
```

For a custom database path, global options come before the command:

```bash
mneme --db .local/live.sqlite3 run --device-backend real --json --input "hello"
```

## Supported Inventory Sources

The real backend uses best-effort OS commands:

- macOS: `system_profiler -json SPCameraDataType SPAudioDataType`
- Windows: PowerShell/CIM inventory for camera, image, audio endpoint, and media devices
- Linux: `v4l2-ctl --list-devices`, `arecord -l`, `aplay -l`, and `pactl list short`

If a command is unavailable, times out, or returns malformed output, Mneme ignores that source and continues.

## Output

Startup JSON includes a device snapshot:

```json
{
  "type": "startup",
  "devices": {
    "available_counts": {
      "camera": 1,
      "microphone": 1,
      "speaker": 1
    }
  }
}
```

Each device has:

- `device_id`: stable fingerprint derived from kind and native identifier or label,
- `kind`: `camera`, `microphone`, or `speaker`,
- `label`: OS-reported human-readable name,
- `available`: inventory availability,
- `confidence`: discovery confidence,
- `metadata`: backend, platform, command source, and native ID when available.

## Deterministic Mode

Fake discovery is still the default:

```bash
mneme run --json --input "hello"
```

Use an empty inventory for no-device tests:

```bash
mneme run --device-backend none --json --input "hello"
```

The older flag remains supported:

```bash
mneme run --no-fake-devices --json --input "hello"
```

## Limitations

- Inventory does not prove permission to capture or play media.
- Linux output depends on which device tools are installed.
- Duplicate physical devices can appear through multiple Linux audio APIs.
- Live frame capture and speech transcription require configured local command adapters; see `docs/runbooks/LIVE_PERCEPTION.md`.
- Speaker output and permission UX remain later-stage work.

## Verification

Run focused tests:

```bash
python -m pytest tests/test_real_peripherals.py tests/test_stage3_runtime.py
```

Run the full project check:

```bash
python scripts/dev_check.py
```
