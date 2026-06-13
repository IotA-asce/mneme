# Risks

- Device discovery is still inventory-only and OS-dependent. If macOS or another host returns no inventory, the UI can refresh but cannot force the OS to expose devices.
- The dialogue planner is more grounded but remains deterministic; local model-backed language generation is still future work.
- Real mic/camera/TTS validation still requires manual local runs with optional dependencies and permissions.
