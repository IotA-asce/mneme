# Sensory Echo and Working Memory Rules

Date: 2026-06-12
Status: Implemented in this feature branch

## Architecture Rules

- Sensory echo stores short-lived fragments, not durable memories.
- Working memory stores active context, not an unbounded conversation log.
- Memory components may observe runtime events but must not command skills or actuators.
- The executive remains the owner of intent; working memory only records active intent context.

## Safety Rules

- Do not add camera, microphone, GPIO, serial, motor, or actuator integration.
- Safety state in working memory is context only, not certified enforcement.
- Do not store secrets in event payloads or snapshots.

## Testing Rules

- Use explicit timestamps for TTL behavior.
- Use temporary SQLite databases for snapshot persistence tests.
- Verify capacity limits and expiry without sleeps.

## Anti-Patterns

- No asyncio for local in-process event handling.
- No global singleton memory state.
- No automatic durable promotion.
- No unbounded dialogue/event history.
