# Executive v0 Rules

## Architectural boundaries

- The executive consumes state.
- The executive publishes intent.
- The executive must not call skill controllers.
- The executive must not call actuator, servo, GPIO, serial, or hardware code.
- Future skills may consume executive intent and publish skill goals.

## Safety constraints

- Safety freeze outranks every ordinary behavior.
- Degraded mode outranks social interaction and memory handling.
- Freeze/degraded intents are coordination signals, not certified hardware safety enforcement.

## Testing expectations

- Priority order must be deterministic.
- Higher-priority safety intents must preempt lower-priority social intents.
- Intent serialization must be JSON-friendly.
- Runtime publication must produce `executive_intent`, not skill events.

## Persistence constraints

- Executive v0 is transient runtime state.
- No storage migration is introduced.

## Anti-patterns

- Do not add LLM calls to the arbitration path.
- Do not add behavior-tree dependencies until the deterministic boundary is stable.
- Do not let attention directly command gaze.
- Do not encode actuator-specific command fields in executive intent.
