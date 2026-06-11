# Risks

## Configuration Risk

Custom thresholds can intentionally change promotion decisions. The no-config default path still uses the original V1 weights and thresholds.

## Boundary Risk

The model layer rejects invalid `SalienceFeatures` at construction. Defensive scorer clamping only exists for mutated or legacy feature objects and is explicitly reported in the explanation payload.

## Mitigation

Keep salience tests focused on boundaries and require documentation updates when scoring factors or threshold policy changes.
