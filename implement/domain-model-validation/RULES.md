# Rules

## Architecture Boundaries

- Models validate and serialize in-process memory data.
- Models do not own SQLite persistence, retrieval ranking, consolidation, ROS transport, or hardware behavior.

## Validation Rules

- Confidence and salience must be finite numbers in `0.0..1.0`.
- Timestamps must be non-negative integers.
- Episode end time must not precede start time.
- Source type and status values must match the documented enums.
- Required IDs and summaries must be non-empty strings.
- Missing optional fields may use defaults, but supplied invalid values must fail.

## Testing Expectations

- Cover constructor validation.
- Cover `from_dict()` validation.
- Cover enum string conversion.
- Cover JSON round trips for public model types.

## Anti-Patterns

- Do not clamp invalid values silently.
- Do not add Pydantic or another validation framework without explicit approval.
- Do not change storage schema as part of this model-boundary change.
- Do not add hardware, ROS runtime, or retrieval behavior to this task.
