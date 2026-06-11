# Risks

## Compatibility Risk

The model constructors now reject invalid data that previously could be stored in dataclass instances. Existing tests and scripts use valid values and continue to pass, but future callers may need to handle `ValueError` when parsing external input.

## Boundary Risk

This change does not update SQLite schema, ROS-style interface drafts, or retrieval behavior. Future work must keep those layers aligned with `docs/memory/MODELS.md` if public fields change.

## Mitigation

Keep validation tests close to the model layer and update the model documentation whenever public fields or serialization shapes change.
