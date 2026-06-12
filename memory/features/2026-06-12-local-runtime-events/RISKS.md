# Risks

- The event bus is in-process only and should not be mistaken for a distributed runtime.
- Safety events are coordination signals, not certified safety enforcement.
- Payloads are JSON-friendly dictionaries in V1; future stable interfaces may need stricter schemas.
- There is no adapter to the existing ROS-style `interfaces/` drafts yet.
- No durable event log or replay storage exists yet.
