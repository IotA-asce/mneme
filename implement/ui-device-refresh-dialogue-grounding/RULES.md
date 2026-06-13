# Rules

- Device refresh must use existing discovery backends and must not open media streams.
- UI remains a visualization/control surface; it must not own cognition.
- Dialogue planner remains deterministic and does not call LLMs or TTS directly.
- Speakability filtering remains enforced before spoken memory references.
- Tests must use fake or in-process backends, not real devices.
