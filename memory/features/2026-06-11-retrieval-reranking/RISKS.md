# Risks

- Context matching is token overlap, not semantic matching.
- Facts still lack first-class salience and recency fields, so those factors are `0.0` for facts until the model/storage contract grows.
- Retrieval history is read from meta-memory but retrieval does not update counters yet.
- Summary candidates are planned by the candidate shape but are not implemented because summary retrieval does not exist yet.
