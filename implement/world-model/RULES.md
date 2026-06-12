# Rules

- State builders publish state: `world_state_update` events only — never intent, skill goals, or safety overrides.
- Deterministic: injected clock, latest-event-wins per state key, sorted snapshot ordering.
- No persistence, no threads, no new dependencies, no schema changes.
- Safety events update the world model's safety view; the world model never originates safety levels.
- Tests first (red); replay fixture snapshot pinned.
- Must not change: perception event payload contracts, existing working-memory/attention consumption of `world_state_update`.
