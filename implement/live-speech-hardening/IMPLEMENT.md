# Live Speech Hardening Implementation

## Phases

1. Add `SpeechLoopDiagnostics` to observe speech transcripts, response generation, speech skill status, duplicate suppressions, barge-ins, latency fields, and stuck states.
2. Wire diagnostics into `MnemeRuntime` snapshots and preserve `LiveSpeechWorker` reports for `no_speech`, `no_microphone`, `capture_error`, and `transcribed`.
3. Add fake-backed speech soak fixtures and `mneme eval speech` for deterministic CLI verification.
4. Extend `EvaluationLogger` with speech-loop metrics.
5. Update README, Local Living Lab docs, repository status, backlog, implementation artifacts, and project memory.

## Files/Modules

- `src/android_brain_memory/speech_loop.py`
- `src/android_brain_memory/speech_benchmarks.py`
- `src/android_brain_memory/runtime_loop.py`
- `src/android_brain_memory/live_perception.py`
- `src/android_brain_memory/presence.py`
- `src/android_brain_memory/evaluation.py`
- `src/android_brain_memory/virtual_head.py`
- `tests/fixtures/speech/`
- `tests/test_speech_loop_hardening.py`

## Validation

Targeted:

```bash
.venv/bin/python -m pytest tests/test_speech_loop_hardening.py tests/test_conversational_presence.py tests/test_live_perception.py tests/test_stage6_local_living_lab.py -q
```

Full:

```bash
git diff --check
.venv/bin/python scripts/dev_check.py
```

Manual remaining:

```bash
mneme run --profile local-speech --tts-command "say {text}" --evaluation-log .local/evaluation/daily_driver.jsonl --json
mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json
```

## Definition of Done

- Runtime JSON includes `speech_loop` diagnostics.
- Duplicate live transcripts inside the configured window do not create duplicate spoken responses.
- No speech, ASR failure, TTS failure, barge-in, and stuck speaking are covered by fake-backed fixtures.
- `mneme eval speech --json` runs the bundled suite.
- README includes a local brain manual.
- Docs, backlog, and memory are updated.

