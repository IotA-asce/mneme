# Rules

- The executive publishes intent only; memory access is read-only retrieval; no motor or skill calls.
- Safety rules stay first and unconditional; goals never delay or weaken freeze/degraded intents — they get suspended, not consulted.
- Memory payloads carry IDs/warnings/provenance text only — never fact/episode content (the dialogue planner consumes `last_memory_bundle` directly in-process).
- v0 contracts preserved: default parameters reproduce v0 behavior exactly; existing tests must pass unmodified.
- Deterministic: injected clock, counter-based idle rotation. Tests first (red).
