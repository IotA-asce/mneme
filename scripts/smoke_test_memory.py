import time

from android_brain_memory import MemoryCandidate, MemoryQuery, MemoryStore, SalienceFeatures, score_candidate, retrieve_memory
from android_brain_memory.models import Episode, Fact, SourceType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / ".local" / "android_brain_memory.sqlite3"
MIGRATION = ROOT / "storage" / "migrations" / "001_init.sql"

store = MemoryStore(DB)
store.apply_migration(MIGRATION)

candidate = MemoryCandidate(
    candidate_id="cand_001",
    candidate_type="user_instruction",
    summary="User wants the android brain to use human-inspired selective memory.",
    source_type=SourceType.USER_CONFIRMED,
    confidence=0.95,
    features=SalienceFeatures(
        novelty=0.8,
        task_relevance=0.9,
        social_relevance=0.6,
        surprise=0.4,
        risk=0.0,
        contradiction=0.0,
        repetition_signal=0.2,
        explicit_remember_flag=1.0,
    ),
    entities=["user"],
    tags=["memory", "architecture"],
)

result = score_candidate(candidate)
trace_id = store.store_raw_trace(candidate.summary, candidate.payload, candidate.source_type, candidate.confidence, result.score)
now = int(time.time())
episode = Episode(
    episode_id="ep_001",
    start_ts=now,
    end_ts=now + 1,
    summary=candidate.summary,
    context={"project": "android_brain", "trace_id": trace_id},
    salience=result.score,
    confidence=candidate.confidence,
    participants=["user"],
    provenance_refs=[trace_id],
)
store.store_episode(episode)
store.upsert_fact(Fact(
    fact_id="fact_001",
    subject="android_brain_memory",
    predicate="design_principle",
    object_value={"value": "experience broadly, store narrowly, summarize aggressively, retrieve by context"},
    confidence=0.95,
    source_type=SourceType.USER_CONFIRMED,
    supporting_episode_ids=[episode.episode_id],
))

bundle = retrieve_memory(store, MemoryQuery(query_text="memory", max_results=3))
print("Salience:", result)
print("Retrieval:", bundle.summary)
for fact in bundle.facts:
    print("Fact:", fact.subject, fact.predicate, fact.object_value)
for ep in bundle.episodes:
    print("Episode:", ep.episode_id, ep.summary)
store.close()
