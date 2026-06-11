# Context

The salience code originally used hardcoded weights and thresholds, even though `config/memory.yaml` already contained matching values. The result exposed weighted components but did not explain raw feature values, threshold bands, or explicit override reasons in a structured way.

This feature keeps the default no-config call path compatible and adds opt-in config loading for callers that want settings from `config/memory.yaml`.
