# Rules

- The manager owns window lifecycle only; `WorkingMemory` content updates are untouched.
- Publishes `world_state_update` (`state_key="context_window"`) events only.
- Deterministic: injected clock, caller-driven `tick()`, no threads.
- Snapshots persist through the existing `WorkingMemory.persist_snapshot()` path — no new persistence code.
- One window at a time; overlapping interactions extend the current window.
- Tests first (red); replay fixture covered.
- Must not change: working memory event handling, snapshot schema, perception contracts.
