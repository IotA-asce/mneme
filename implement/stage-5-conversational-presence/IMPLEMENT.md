# Stage 5 Conversational Presence Implementation

## Plan

1. Add a virtual presence module with speech output backends, avatar state, virtual skill goals/records, virtual skill runner, and a coordinator that maps executive/dialogue output to skill goals.
2. Wire virtual presence into `MnemeRuntime` behind an enabled-by-default flag.
3. Add CLI flags for local TTS command, TTS timeout, speech voice, virtual speech duration, and disabling virtual presence.
4. Persist speech voice selection as procedural memory and reuse it on later runs.
5. Add deterministic tests for command substitution, virtual skill status transitions, runtime speech/avatar state, voice persistence, barge-in, safety/avatar state, and CLI JSON output.
6. Update README, runbooks, roadmap/status docs, backlog, and durable project memory.

## Files Changed

- `src/android_brain_memory/presence.py`
- `src/android_brain_memory/runtime_loop.py`
- `src/android_brain_memory/virtual_head.py`
- `src/android_brain_memory/__init__.py`
- `tests/test_conversational_presence.py`
- `README.md`
- `docs/runbooks/CONVERSATIONAL_PRESENCE.md`
- `docs/runbooks/VIRTUAL_HEAD.md`
- `docs/architecture/MASTER_ROADMAP.md`
- `docs/architecture/REPO_STATUS.md`
- `tasks/backlog.md`
- `memory/features/2026-06-13-stage-5-conversational-presence/`

## Validation

- Focused Stage 5/runtime tests:

```bash
python -m pytest tests/test_conversational_presence.py tests/test_stage3_runtime.py tests/test_live_perception.py
```

- Full project check:

```bash
python scripts/dev_check.py
```

- CLI smoke:

```bash
mneme --db /tmp/mneme-stage5-cli.sqlite3 run --json --tts-command "printf {text}" --voice soft --input "hello Mneme"
```

## Rollback

Disable `enable_virtual_presence` construction in `MnemeRuntime`, remove the Stage 5 CLI flags, remove `presence.py` exports/tests/docs, and leave Stage 3/4 typed/live perception behavior intact.

## Definition of Done

- Dialogue plans produce virtual speech goals exactly once per user turn.
- Simulated and command-backed speech outputs are represented in JSON.
- Avatar state reflects attention, speech, completion, and safety.
- User speech during active virtual speech produces preemption.
- Speech voice selection persists through procedural memory.
- No real actuator or hardware control path is introduced.
- Docs, backlog, memory, and verification are updated.
