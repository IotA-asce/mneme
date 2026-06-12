# Context

Phase 6 was the last unimplemented phase of `docs/IMPLEMENTATION_PLAN.md`. The interface drafts under `interfaces/` were written before most of the memory system existed and had drifted: missing fact tags/supersession, no summaries or ranking explanations in bundles, no structured query filters, a `MemoryCandidate` shape with fields the model never had (`source_node`, `ttl`, bare `salience`), and no runtime event message at all.

Design decisions:

- Models own truth; drafts follow models. Fields that exist only in storage (`Fact.last_confirmed_ts`) or are derived (`RuntimeEvent.expires_at`) are intentionally absent from the drafts and the exclusions are explicit in the contract test.
- Dict-valued fields map to `*_json` strings rather than nested typed messages, matching the project's "early prototypes may use JSON payloads" rule while keeping enum/string/scalar fields typed.
- The contract test asserts alignment in both directions so neither models nor drafts can drift silently.
- ROS work remains deferred per the roadmap; the launch plan stages it behind replay-test stability and keeps the local event bus as the permanent regression harness.
- Per AGENTS.md, no architecture theater: no colcon/ament files, no QoS configs, no launch files yet.
