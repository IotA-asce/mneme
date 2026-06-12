# Local Runtime Events

Type: Feature
Date: 2026-06-12
Status: Complete

## Summary

Added a lightweight local runtime event model and synchronous in-process event bus:

- explicit runtime event kinds for perception, world state, attention, memory, executive, skill, and safety boundaries,
- JSON-friendly `RuntimeEvent` dataclass,
- helper constructors for each required event category,
- deterministic `EventBus` with sequence ordering, subscription filters, history, and TTL expiry,
- tests for publication, subscription, filtering, ordering, expiry, validation, and serialization,
- runtime architecture documentation.

No ROS 2 integration, asyncio, cross-process transport, persistence, hardware control, or new dependency was added.
