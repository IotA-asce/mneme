# Changes

- Added `presence.py` with speech output backends, virtual avatar state, virtual skill records, a virtual skill runner, and a conversational presence coordinator.
- Wired virtual presence into `MnemeRuntime` and exposed presence state in runtime snapshots.
- Added CLI flags for local TTS command, TTS timeout, speech voice, virtual speech duration, and disabling virtual presence.
- Persisted speech voice selection as procedural memory and reused it on later runs.
- Added tests for command substitution, virtual speech status order, avatar state, voice persistence, barge-in preemption, safety/avatar handling, and CLI JSON output.
- Updated README, runbooks, roadmap/status docs, backlog, and implementation records.
