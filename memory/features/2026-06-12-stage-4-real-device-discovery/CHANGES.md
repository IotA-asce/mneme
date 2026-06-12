# Changes

- Added `RealPeripheralBackend` implementing the existing peripheral discovery interface.
- Added best-effort parsing for macOS `system_profiler`, Windows PowerShell/CIM, and Linux `v4l2-ctl`/ALSA/PulseAudio inventory tools.
- Added `mneme run --device-backend real` and kept fake discovery as the default.
- Added tests for injected macOS, Linux, and Windows command output.
- Documented real discovery scope and limitations.
