# Context

The user ran Mneme with:

```bash
mneme run --profile local-lab --live \
  --asr-model .local/models/faster-whisper-base \
  --face-backend mediapipe \
  --tts-command "say {text}"
```

Model files were placed locally:

- `.local/models/faster-whisper-base`
- `.local/models/mediapipe/face_detector.task`

Kokoro remained missing, but macOS `say` provided speech output for this run.

