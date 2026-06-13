# Changes

- Added `003_memory_review.sql` with durable review records.
- Added storage methods for writing, listing, reading, and updating review records.
- Added review apply/reject helpers for correction, forget, confirmation, and contradiction review.
- Added `confirm_memory_request` turn classification.
- Runtime review proposals now persist and include a `review_id`.
- Added `mneme review list/show/apply/reject/conflicts/explain`.
- `mneme eval cognition --json` now runs the bundled cognition suite by default.
- Added benchmark fixtures for delayed recall, hallucination guard, correction approval, forget suppression, contradiction review, and self/status questions.
- Updated UI to show latest review state and submit review apply/reject actions.
