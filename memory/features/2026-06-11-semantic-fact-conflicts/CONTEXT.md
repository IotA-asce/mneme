# Context

Mneme's design requires semantic memory to distinguish confirmed facts, inferred beliefs, superseded facts, and conflicted facts. The storage schema already had `status` and `supersedes_fact_id`, but the upsert path did not use those fields for truth handling.

This change implements a conservative first pass. It avoids broad contradiction claims by only checking `user_confirmed` and `model_inferred` truth assertions, and by preserving facts with different context envelopes as non-conflicting.
