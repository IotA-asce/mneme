# Memory CLI Runbook

Status: V1 local memory API and CLI

This runbook describes the high-level Mneme memory command surface. It is bench-only: it does not start ROS 2, call an LLM, use vector search, or control robot hardware.

## Entry Points

Use the repository wrapper:

```bash
python scripts/mneme_memory.py --help
```

Or use the package module:

```bash
python -m android_brain_memory.cli --help
```

Both entry points produce JSON for successful commands.

## Database Options

By default, commands use:

```text
.local/android_brain_memory.sqlite3
storage/migrations/
```

Use a temporary or alternate database with:

```bash
python scripts/mneme_memory.py --db /tmp/mneme.sqlite3 init-db
```

All commands other than `init-db` also run migrations before doing work, so a new local database can be used directly.

## Commands

Initialize the database:

```bash
python scripts/mneme_memory.py init-db
```

Inspect counts and recent summary metadata:

```bash
python scripts/mneme_memory.py inspect-db
```

Retrieve by text:

```bash
python scripts/mneme_memory.py retrieve --query-text calibration --max-results 5
```

Retrieve by structured fact filters:

```bash
python scripts/mneme_memory.py retrieve \
  --fact-subject user \
  --fact-predicate prefers \
  --tag preference
```

Run one deterministic consolidation pass:

```bash
python scripts/mneme_memory.py consolidate-once --min-repetition 3
```

## JSON Payload Commands

`remember-candidate`, `add-episode`, and `add-fact` accept either `--data` with a JSON object or `--file` with a JSON file path.

Score and store a memory candidate:

```bash
python scripts/mneme_memory.py remember-candidate --file candidate.json
```

Score, store a raw trace, and encode/store an episode:

```bash
python scripts/mneme_memory.py remember-candidate \
  --file candidate.json \
  --episode \
  --episode-id ep_example_001 \
  --start-ts 100 \
  --end-ts 110 \
  --participant user \
  --context-json '{"topic": "calibration routine", "tags": ["calibration"]}'
```

Add an episode:

```bash
python scripts/mneme_memory.py add-episode --file episode.json
```

Add or upsert a fact:

```bash
python scripts/mneme_memory.py add-fact --file fact.json
```

## Candidate JSON Shape

Candidate payloads use the same shape as `MemoryCandidate.to_dict()`:

```json
{
  "candidate_id": "cand_001",
  "candidate_type": "dialogue_turn",
  "summary": "User asked Mneme to remember the calibration routine.",
  "source_type": "user_confirmed",
  "confidence": 0.95,
  "features": {
    "novelty": 0.8,
    "task_relevance": 0.9,
    "social_relevance": 0.4,
    "surprise": 0.3,
    "risk": 0.0,
    "contradiction": 0.0,
    "repetition_signal": 0.7,
    "explicit_remember_flag": 1.0
  },
  "entities": ["user"],
  "tags": ["calibration"],
  "payload": {
    "topic": "calibration routine"
  },
  "provenance_refs": []
}
```

## Episode JSON Shape

Episode payloads use the same shape as `Episode.to_dict()`:

```json
{
  "episode_id": "ep_calibration_001",
  "start_ts": 100,
  "end_ts": 110,
  "summary": "User practiced the calibration routine with Mneme.",
  "context": {
    "topic": "calibration routine",
    "tags": ["calibration"]
  },
  "salience": 0.82,
  "confidence": 0.9,
  "participants": ["user"],
  "objects": [],
  "provenance_refs": []
}
```

## Fact JSON Shape

Fact payloads use the same shape as `Fact.to_dict()`:

```json
{
  "fact_id": "fact_calibration_routine",
  "subject": "user",
  "predicate": "practices",
  "object_value": {
    "value": "calibration routine"
  },
  "confidence": 0.95,
  "source_type": "user_confirmed",
  "status": "active",
  "tags": ["calibration"],
  "supporting_episode_ids": ["ep_calibration_001"],
  "supersedes_fact_id": null
}
```

## Facade API

Python callers can use `MnemeMemory` directly:

```python
from android_brain_memory import MnemeMemory

with MnemeMemory() as memory:
    memory.init_db()
    remembered = memory.remember_candidate(candidate_payload, create_episode=True)
    bundle = memory.retrieve({"query_text": "calibration", "max_results": 5})
    report = memory.consolidate_once({"min_repetition": 3})
```

The facade delegates validation to the existing dataclasses and delegates behavior to existing storage, salience, retrieval, and consolidation modules.

## V1 Boundaries

- `remember-candidate` scores and stores structured candidates; it does not parse arbitrary prose into facts.
- `add-fact` preserves conflict handling in `MemoryStore.upsert_fact()`.
- `retrieve` returns facts and episodes through the current deterministic retrieval layer. Summary retrieval remains future work.
- `consolidate-once` creates deterministic summaries for repeated episode groups and preserves source episodes.
- CLI JSON should not include secrets, tokens, private keys, credentials, or hardware control data.
