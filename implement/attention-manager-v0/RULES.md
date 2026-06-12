# Attention Manager v0 Rules

## Architectural boundaries

- The Attention Manager consumes observations and state events.
- The Attention Manager publishes attention state.
- It must not publish skill goals, actuator commands, servo targets, or gaze commands.
- Skills may later decide how to move from attention state.

## Safety constraints

- Safety-relevant events can override ordinary focus.
- Safety attention remains a state signal; actuator suppression belongs to safety/actuator layers.
- No live hardware commands are allowed in this feature.

## Testing expectations

- Tests must cover deterministic ordering and explainable state.
- Dwell behavior must prevent rapid flicker.
- Expired targets must be released.

## Persistence constraints

- V0 attention state is transient runtime state.
- No migration or durable attention table is introduced.

## Anti-patterns

- Do not make perception workers directly command gaze.
- Do not turn attention state into an unbounded event log.
- Do not use an LLM or vector search for attention ranking in this phase.
- Do not encode actuator-specific fields in attention targets.
