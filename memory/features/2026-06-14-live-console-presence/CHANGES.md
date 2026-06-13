# Changes

- Added live status streaming to `mneme run --live`.
- Routed live status to stderr when `--json` is active so stdout remains valid JSON.
- Added `--quiet-live-status` for machine-only live JSON runs.
- Summarized camera frames, disabled face detection, person observations, speech transcripts, no-speech states, missing microphones, ASR/capture failures, attention target, and virtual presence state.
- Added failure hints for common speech setup issues such as invalid faster-whisper model paths, missing optional dependencies, and microphone permission failures.
- Updated README and live runbooks to explain why local vision can be active without person tracking and why speech may not respond when ASR fails.
- Added tests that prove live speech/vision status is streamed while JSON output remains parseable.

