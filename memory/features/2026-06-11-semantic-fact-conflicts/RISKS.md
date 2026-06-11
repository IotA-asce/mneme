# Risks and Follow-Up

- V1 conflict detection is deterministic and conservative; it does not understand natural language contradictions.
- Only `user_confirmed` and `model_inferred` assertions participate in conflict detection to avoid broad false positives.
- `supersedes_fact_id` records one direct predecessor. A future relation table may be needed for many-to-many supersession.
- Conflict reports are review/debug aids; no user clarification workflow exists yet.
