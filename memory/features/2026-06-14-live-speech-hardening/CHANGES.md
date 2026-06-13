# Changes

- Added `SpeechLoopDiagnostics` for runtime speech-loop state, counters, latest reports, latency fields, duplicate suppression, barge-ins, and stuck states.
- Added ASR timing and clearer capture error details to live speech worker reports.
- Added TTS timing/output metadata to virtual speech skill completion/failure statuses.
- Suppressed duplicate live/external transcripts inside a short deterministic window while preserving typed input and later follow-up turns.
- Added fake-backed speech soak fixtures and `mneme eval speech`.
- Extended daily-driver evaluation records and summaries with speech-loop metrics.
- Updated README, Local Living Lab runbook, repository status, cognitive capability roadmap, backlog, and implementation artifacts.

