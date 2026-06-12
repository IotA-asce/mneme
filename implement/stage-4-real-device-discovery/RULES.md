# Stage 4 Real Device Discovery Rules

- Discovery may inventory devices only.
- Discovery must not open a camera stream, record microphone audio, play audio, or request actuator behavior.
- Fake discovery remains the default for deterministic tests and CI.
- Real discovery must be best-effort and timeout-bounded.
- Missing OS tools, unsupported platforms, permission denial, and malformed output must result in an empty or partial inventory, not runtime failure.
- Device metadata must indicate that the backend is real and preserve the platform/source used for discovery.
- Future live perception workers must consume discovered devices through explicit worker configuration rather than bypassing the runtime boundary.
