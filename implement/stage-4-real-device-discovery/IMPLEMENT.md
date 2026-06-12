# Stage 4 Real Device Discovery Implementation

## Plan

1. Add a `RealPeripheralBackend` implementing the existing discovery interface.
2. Parse best-effort device inventories from standard OS tools:
   - macOS: `system_profiler`
   - Windows: PowerShell/CIM
   - Linux: `v4l2-ctl`, `arecord`, `aplay`, `pactl`
3. Expose real discovery through `mneme run --device-backend real`.
4. Keep fake discovery as the default backend.
5. Add tests with injected command output.
6. Document scope and limitations.

## Files Changed

- `src/android_brain_memory/peripherals.py`
- `src/android_brain_memory/runtime_loop.py`
- `src/android_brain_memory/virtual_head.py`
- `src/android_brain_memory/__init__.py`
- `tests/test_real_peripherals.py`
- `docs/runbooks/REAL_DEVICE_DISCOVERY.md`
- `docs/runbooks/VIRTUAL_HEAD.md`
- `docs/architecture/MASTER_ROADMAP.md`
- `docs/architecture/REPO_STATUS.md`
- `tasks/backlog.md`

## Validation

- Focused peripheral and runtime tests.
- Full pytest suite.
- Developer check script.
- Manual JSON CLI inventory command.

## Rollback

Remove `RealPeripheralBackend` and the CLI `--device-backend real` option. Fake discovery remains compatible with Stage 3.

## Definition of Done

- Real discovery can be invoked from the CLI.
- Missing tools or unsupported platforms produce an empty inventory, not a crash.
- Fake discovery remains default and deterministic.
- Stage 4 documentation explicitly says live capture is not implemented yet.
