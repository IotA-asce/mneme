# Rules

## Architectural Boundaries

- Interface drafts are contracts, not runtime bindings: no ROS imports, no generated code, no colcon/ament build files.
- Models own truth; drafts follow models. Never change a domain model to satisfy a draft.
- Runtime event topic boundaries (`EVENT_KIND_TOPICS`) must map 1:1 onto the planned ROS topic namespaces.

## Safety Constraints

- The launch plan must keep the safety supervisor able to override every stage and must not introduce perception-to-actuator shortcuts.
- No hardware-facing behavior is added by this change.

## Testing Expectations

- Contract test written first and observed failing against the stale drafts.
- Alignment is asserted in both directions; derived-field exclusions must be explicit constants in the test, not silent skips.
- JSON round-trips must go through `json.dumps`/`json.loads`, not just dict copies.

## Performance Constraints

- None meaningful; the contract test reads a handful of small text files.

## Persistence / Migration Rules

- No schema or migration changes.

## Anti-Patterns

- Architecture theater: do not add ROS packages, QoS configs, or launch files before the prototype needs them.
- Loose contracts: do not map dict-valued model fields to anything other than `*_json` string fields.
- Silent drift: do not weaken the contract test to "subset" checks.

## What Must Not Change

- Domain model field names and `to_dict()` output shapes.
- Runtime event kinds and topic boundary validation.
- Existing test behavior.
