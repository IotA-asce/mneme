# Context

A local-lab JSON dump showed that Mneme was not actually idle: the camera was capturing frames, attention was curiosity scanning, and the avatar state existed. The experience still felt silent because `--json` produced the useful details only at shutdown and speech was failing before a transcript reached the runtime.

The dump also showed two setup gaps that need to be visible during live runs:

- OpenCV camera capture can work without `--face-backend mediapipe`, but that only produces `camera_frame` events, not `person_seen` events.
- The local speech path can fail before transcription, for example with an ASR model/path validation error, so no dialogue or speech response is produced.

This feature improves the operator-facing "living loop" without changing the architecture boundary: perception still publishes observations, attention/executive/dialogue still decide behavior, and virtual skills still own speech/status output.

