# Rules

- Creating a review proposal must not mutate durable memory.
- Applying a correction may write only a deterministic `user_confirmed` fact.
- Applying a forget request suppresses related memories; it must not delete or purge rows.
- Confirmation upgrades only safe fact references and must not automatically resolve confirmed-vs-confirmed conflicts.
- The UI may request review actions, but it must not own cognition or memory policy.
- Benchmarks must use fake/local deterministic paths only.
