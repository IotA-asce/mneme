# Stage 3 Runtime and Virtual Head Rules

## Architectural boundaries

- The runtime wires components; it does not collapse their responsibilities.
- Perception still publishes observations.
- World and attention publish state.
- Executive publishes intent.
- Dialogue planner renders utterance plans.
- Memory lifecycle components handle storage and retrieval.

## Safety constraints

- No hardware commands.
- No real device capture.
- No ROS runtime.
- Missing devices must be represented as empty inventory, not as crashes.

## Testing expectations

- Runtime behavior must be deterministic with injected timestamps.
- Fake device appearance, removal, and absence must be covered.
- CLI scripted mode must be testable without stdin interaction.
- Scenario replay must still flow through memory, attention, executive, and dialogue paths.

## Anti-patterns

- Do not add heavyweight perception dependencies in Stage 3.
- Do not implement platform-specific discovery above the backend interface.
- Do not make dialogue or executive own storage details directly.
- Do not add any actuator-facing code.
