# Testing

Validation commands for this feature:

```bash
python -m pytest tests/test_salience.py
python -m pytest
python scripts/dev_check.py
git diff --check
```

Expected coverage:

- below `0.25`,
- exactly `0.25`,
- exactly `0.55`,
- exactly `0.80`,
- explicit remember override,
- config file loading,
- custom thresholds,
- detailed explanation payload,
- defensively clamped feature values.
