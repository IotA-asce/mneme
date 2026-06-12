# Memory Consolidation

Status: V1 deterministic SQLite skeleton

Consolidation compresses repeated episode patterns into summaries without deleting source episodes. This phase is intentionally local, deterministic, and inspectable.

## Boundary

The V1 consolidation layer owns:

- one-shot `consolidate_once(store, options)` execution,
- deterministic grouping of recent active episodes,
- deterministic summary text generation,
- writing `memory_summary` records,
- preserving source episodes,
- writing decay/downranking metadata into meta-memory.

It does not own:

- long-running scheduling,
- LLM summarization,
- fact extraction,
- contradiction review,
- purge or deletion,
- retrieval use of decay metadata.

## Entry Point

```python
from android_brain_memory import ConsolidationOptions, consolidate_once

report = consolidate_once(
    store,
    ConsolidationOptions(min_repetition=3),
)
```

The manual script runs one pass:

```bash
python scripts/consolidate_once.py
```

## Grouping Rules

The pass examines recent active episodes and creates candidate groups from deterministic cues:

- shared context tags from `episode.context["tag"]` or `episode.context["tags"]`,
- shared participants plus similar topic text,
- similar topic text from summary and context topic fields,
- close time windows plus shared participants.

Candidate groups are sorted deterministically. Once a group creates a summary, its episodes are not reused by another group in the same pass.

## Summary Creation

Groups must meet `ConsolidationOptions.min_repetition`.

Summaries are written with:

- `summary_type="repeated_episode_group"`,
- deterministic `summary_id`,
- deterministic `scope_key`,
- support links in summary meta-memory provenance,
- start/end timestamps spanning the grouped episodes.

The summary text is deliberately simple and deterministic. It includes the group size, group label, participant set, time span, and representative episode summary.

## Episode Preservation

Consolidation does not delete, suppress, or mutate source episode rows. Representative episodes remain ordinary active episodes.

## Decay Metadata

This phase uses `meta_memory.provenance_json["decay"]` instead of a new migration.

Non-representative episodes covered by a summary receive metadata like:

```json
{
  "policy": "covered_by_summary",
  "accessibility": "downrank_candidate",
  "summary_id": "summary_abc123",
  "representative_episode_id": "ep_001",
  "updated_ts": 1234567890
}
```

Retrieval does not consume this metadata yet. It is a documented hook for future accessibility decay and downranking.

## Report

`ConsolidationReport` includes:

- `episodes_examined`
- `groups_considered`
- `groups_summarized`
- `summaries_created`
- `summaries_updated`
- `facts_created`
- `conflicts_flagged`
- `decay_metadata_updates`
- `summary_ids`
- `notes`

## Daemon

`ConsolidationDaemon` wraps the one-shot pass with scheduling, bounds, and observability:

- `tick(now_ms=None)` runs a pass only when `min_interval_s` has elapsed since the last pass; otherwise it counts a skipped tick and returns `None`.
- `run_once(now_ms=None)` forces a pass regardless of interval.
- Batch size is bounded by the configured `ConsolidationOptions.max_episodes`.
- Each pass publishes a `memory_lifecycle` event (`lifecycle_stage="consolidation"`) with the report counts and summary IDs.
- `stats` accumulates passes, skipped ticks, last-run time, and cumulative summary/decay counts.

The daemon is deterministic by construction: time arrives through an injected clock and callers drive `tick()` — no threads, timers, or sleeps. A future runtime loop or ROS timer (Stage 3) simply calls `tick()` periodically. Repeated passes over unchanged episodes update existing summaries rather than duplicating them because summary IDs are content-derived.

## Testing

Current tests create repeated tagged episodes, run one consolidation pass, verify one summary row is created, verify source episodes remain active, and verify decay metadata is written through meta-memory. Daemon tests (`tests/test_consolidation_daemon.py`) cover the interval policy, forced runs, idempotent repeat passes, batch limits, lifecycle events, and stat accumulation under a fixed injected clock.
