# Memory Review

Status: M8.5 / M10.1 supervised review loop

Mneme uses memory review records when the user challenges, corrects, confirms, or asks to forget a memory-backed response. A review record is durable, auditable, and separate from the memory item itself.

## Review Types

- `correction`: a user says the previous answer was wrong or provides a corrected fact.
- `forget_request`: a user asks Mneme to forget the referenced memory.
- `confirm_memory`: a user confirms the referenced memory.
- `contradiction_challenge`: a user challenges conflicting memory.

Statuses are `proposed`, `applied`, `rejected`, and `failed`.

## Safety Rules

Creating a review proposal never changes memory. Applying a review is explicit:

- Correction applies only when a deterministic fact payload is available.
- Forget suppresses related facts and supporting episodes; it does not purge rows.
- Confirm upgrades safe fact references to `user_confirmed`.
- Confirmed-vs-confirmed contradictions remain preserved for review.

## Commands

```bash
mneme review list --json
mneme review show --review-id review_... --json
mneme review apply --review-id review_... --reason "user approved" --json
mneme review reject --review-id review_... --reason "not correct" --json
mneme review conflicts --json
mneme review explain --memory-kind fact --memory-id fact_... --json
```

For correction records that cannot be parsed from the original turn, pass a deterministic fact payload:

```bash
mneme review apply \
  --review-id review_... \
  --reason "user corrected preference" \
  --fact-data '{"subject":"user","predicate":"likes","value":"coffee"}' \
  --json
```

## UI

`mneme ui` shows the latest review id, type, and status. Buttons submit the same review turns used in terminal mode, and Apply/Reject call the review backend directly.

## Benchmarking

`mneme eval cognition --json` runs the bundled suite, including correction approval, forget suppression, contradiction review, delayed recall, hallucination guard, and self/status questions.
