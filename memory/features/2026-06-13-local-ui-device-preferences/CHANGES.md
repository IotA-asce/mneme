# Changes

- Added JSON-backed `RuntimePreferencesStore` and `RuntimeDevicePreferences`.
- Added runtime update/load support for selected camera, microphone, and speaker IDs.
- Taught live vision and live speech workers to prefer selected devices and fall back when unavailable.
- Taught conversational presence to pass the preferred speaker device ID into speech goals.
- Added `--camera-device-id`, `--microphone-device-id`, and `--speaker-device-id` terminal overrides.
- Changed `mneme ui` to use real device inventory by default for selectors.
- Reworked the local UI into a cleaner minimal state surface with device selectors and live `/state` refresh.
- Updated README, Local Living Lab runbook, repo status, backlog, implementation notes, and memory index.
