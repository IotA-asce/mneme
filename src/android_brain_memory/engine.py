from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
import time
import uuid
from typing import Any

from .consolidation import ConsolidationOptions, ConsolidationReport, consolidate_once
from .models import (
    Episode,
    Fact,
    MemoryBundle,
    MemoryCandidate,
    MemoryQuery,
    SalienceResult,
    SourceType,
    Speakability,
)
from .retrieval import retrieve_memory
from .salience import SalienceScoringConfig, score_candidate
from .storage import FactConflictReport, MemoryStore, MigrationRecord


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / ".local" / "android_brain_memory.sqlite3"
DEFAULT_MIGRATIONS = ROOT / "storage" / "migrations"

INSPECT_TABLES = (
    "schema_migration",
    "raw_trace",
    "episode",
    "episode_entity",
    "fact",
    "fact_support",
    "fact_tag",
    "memory_summary",
    "meta_memory",
    "working_context_snapshot",
)


@dataclass(slots=True)
class RememberCandidateResult:
    candidate: MemoryCandidate
    salience: SalienceResult
    trace_id: str | None = None
    episode: Episode | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "salience": self.salience.to_dict(),
            "trace_id": self.trace_id,
            "episode": self.episode.to_dict() if self.episode else None,
        }


@dataclass(slots=True)
class FactUpsertResult:
    fact: Fact
    conflict_report: FactConflictReport | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact.to_dict(),
            "conflict_report": to_jsonable(self.conflict_report) if self.conflict_report else None,
        }


class MnemeMemory:
    """High-level facade over Mneme's local memory primitives."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB,
        *,
        migrations_dir: str | Path | None = DEFAULT_MIGRATIONS,
        store: MemoryStore | None = None,
    ) -> None:
        self.migrations_dir = Path(migrations_dir) if migrations_dir is not None else None
        self.store = store if store is not None else MemoryStore(db_path)
        self.db_path = self.store.db_path
        self._owns_store = store is None

    def __enter__(self) -> "MnemeMemory":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def init_db(self) -> list[MigrationRecord]:
        if self.migrations_dir is None:
            raise ValueError("migrations_dir is required to initialize the database")
        return self.store.run_migrations(self.migrations_dir)

    def remember_candidate(
        self,
        candidate: MemoryCandidate | Mapping[str, Any],
        *,
        config: SalienceScoringConfig | None = None,
        config_path: str | Path | None = None,
        store_trace: bool = True,
        create_episode: bool = False,
        episode_id: str | None = None,
        start_ts: int | None = None,
        end_ts: int | None = None,
        participants: list[str] | None = None,
        objects: list[str] | None = None,
        context: Mapping[str, Any] | None = None,
        source_id: str | None = None,
        speakability: Speakability | str = Speakability.NORMAL,
        notes: str | None = None,
    ) -> RememberCandidateResult:
        memory_candidate = _coerce_candidate(candidate)
        salience = score_candidate(
            memory_candidate,
            config=config,
            config_path=config_path,
        )
        trace_id = None
        if store_trace:
            trace_id = self.store.store_raw_trace(
                memory_candidate.summary,
                {"candidate": memory_candidate.to_dict()},
                memory_candidate.source_type,
                memory_candidate.confidence,
                salience.score,
                source_id=source_id or memory_candidate.candidate_id,
                derivation_path=["candidate", "salience_score"],
                supporting_memory_ids=memory_candidate.provenance_refs,
                notes=notes,
                speakability=speakability,
            )

        episode = None
        if create_episode:
            episode = self.encode_episode(
                memory_candidate,
                salience,
                trace_id=trace_id,
                episode_id=episode_id,
                start_ts=start_ts,
                end_ts=end_ts,
                participants=participants,
                objects=objects,
                context=context,
            )
            supporting_memory_ids = list(episode.provenance_refs)
            self.store.store_episode(
                episode,
                source_type=memory_candidate.source_type,
                source_id=source_id or memory_candidate.candidate_id,
                derivation_path=["candidate", "salience_score", "episode"],
                supporting_memory_ids=supporting_memory_ids,
                notes=notes,
                speakability=speakability,
            )

        return RememberCandidateResult(
            candidate=memory_candidate,
            salience=salience,
            trace_id=trace_id,
            episode=episode,
        )

    def encode_episode(
        self,
        candidate: MemoryCandidate | Mapping[str, Any],
        salience: SalienceResult | Mapping[str, Any],
        *,
        trace_id: str | None = None,
        episode_id: str | None = None,
        start_ts: int | None = None,
        end_ts: int | None = None,
        participants: list[str] | None = None,
        objects: list[str] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Episode:
        memory_candidate = _coerce_candidate(candidate)
        salience_result = _coerce_salience_result(salience)
        started = start_ts if start_ts is not None else int(time.time())
        ended = end_ts if end_ts is not None else started
        episode_context = dict(memory_candidate.payload)
        if context is not None:
            episode_context.update(dict(context))
        episode_context.setdefault("candidate_id", memory_candidate.candidate_id)
        episode_context.setdefault("candidate_type", memory_candidate.candidate_type)
        if memory_candidate.tags:
            episode_context.setdefault("tags", list(memory_candidate.tags))
        if trace_id is not None:
            episode_context.setdefault("trace_id", trace_id)
        provenance_refs = list(memory_candidate.provenance_refs)
        if trace_id is not None:
            provenance_refs.append(trace_id)

        return Episode(
            episode_id=episode_id or f"ep_{uuid.uuid4().hex[:12]}",
            start_ts=started,
            end_ts=ended,
            summary=memory_candidate.summary,
            context=episode_context,
            salience=salience_result.score,
            confidence=memory_candidate.confidence,
            participants=(
                list(participants)
                if participants is not None
                else list(memory_candidate.entities)
            ),
            objects=list(objects) if objects is not None else [],
            provenance_refs=provenance_refs,
        )

    def add_episode(
        self,
        episode: Episode | Mapping[str, Any],
        *,
        source_type: SourceType | str = SourceType.SYSTEM_GENERATED,
        source_id: str | None = None,
        derivation_path: list[str] | None = None,
        supporting_memory_ids: list[str] | None = None,
        speakability: Speakability | str = Speakability.NORMAL,
        notes: str | None = None,
    ) -> Episode:
        stored_episode = _coerce_episode(episode)
        self.store.store_episode(
            stored_episode,
            source_type=source_type,
            source_id=source_id,
            derivation_path=derivation_path or ["episode"],
            supporting_memory_ids=supporting_memory_ids
            if supporting_memory_ids is not None
            else stored_episode.provenance_refs,
            speakability=speakability,
            notes=notes,
        )
        return stored_episode

    def add_fact(
        self,
        fact: Fact | Mapping[str, Any],
        *,
        source_id: str | None = None,
        derivation_path: list[str] | None = None,
        supporting_memory_ids: list[str] | None = None,
        speakability: Speakability | str = Speakability.NORMAL,
        notes: str | None = None,
    ) -> FactUpsertResult:
        stored_fact = _coerce_fact(fact)
        conflict_report = self.store.upsert_fact(
            stored_fact,
            source_id=source_id,
            derivation_path=derivation_path or ["fact"],
            supporting_memory_ids=supporting_memory_ids
            if supporting_memory_ids is not None
            else stored_fact.supporting_episode_ids,
            speakability=speakability,
            notes=notes,
        )
        refreshed = self.store.get_fact(stored_fact.fact_id) or stored_fact
        return FactUpsertResult(fact=refreshed, conflict_report=conflict_report)

    def retrieve(self, query: MemoryQuery | Mapping[str, Any] | str) -> MemoryBundle:
        return retrieve_memory(self.store, _coerce_query(query))

    def consolidate_once(
        self,
        options: ConsolidationOptions | Mapping[str, Any] | None = None,
    ) -> ConsolidationReport:
        return consolidate_once(self.store, options)

    def inspect_db(self) -> dict[str, Any]:
        return {
            "db_path": str(self.db_path),
            "applied_migrations": to_jsonable(self.store.get_applied_migrations()),
            "table_counts": {
                table: self._table_count(table)
                for table in INSPECT_TABLES
                if self._table_exists(table)
            },
            "facts_by_status": self._group_counts("fact", "status"),
            "facts_by_source_type": self._group_counts("fact", "source_type"),
            "episodes_by_status": self._group_counts("episode", "status"),
            "meta_memory_by_kind": self._group_counts("meta_memory", "memory_kind"),
            "summaries_by_type": self._group_counts("memory_summary", "summary_type"),
            "recent_summaries": to_jsonable(self.store.get_memory_summaries(limit=5))
            if self._table_exists("memory_summary")
            else [],
        }

    def _table_exists(self, table_name: str) -> bool:
        row = self.store.conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_count(self, table_name: str) -> int:
        if table_name not in INSPECT_TABLES:
            raise ValueError(f"unsupported inspect table: {table_name}")
        row = self.store.conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])

    def _group_counts(self, table_name: str, column_name: str) -> dict[str, int]:
        if table_name not in INSPECT_TABLES:
            raise ValueError(f"unsupported inspect table: {table_name}")
        if not self._table_exists(table_name):
            return {}
        row = self.store.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = {item["name"] for item in row}
        if column_name not in columns:
            return {}
        rows = self.store.conn.execute(
            f"""
            SELECT {column_name} AS key, COUNT(*) AS count
            FROM {table_name}
            GROUP BY {column_name}
            ORDER BY {column_name}
            """
        ).fetchall()
        return {item["key"]: int(item["count"]) for item in rows}


MemoryEngine = MnemeMemory


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        return to_jsonable(value.to_dict())
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(nested) for key, nested in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _coerce_candidate(candidate: MemoryCandidate | Mapping[str, Any]) -> MemoryCandidate:
    if isinstance(candidate, MemoryCandidate):
        return candidate
    return MemoryCandidate.from_dict(candidate)


def _coerce_salience_result(salience: SalienceResult | Mapping[str, Any]) -> SalienceResult:
    if isinstance(salience, SalienceResult):
        return salience
    return SalienceResult.from_dict(salience)


def _coerce_episode(episode: Episode | Mapping[str, Any]) -> Episode:
    if isinstance(episode, Episode):
        return episode
    return Episode.from_dict(episode)


def _coerce_fact(fact: Fact | Mapping[str, Any]) -> Fact:
    if isinstance(fact, Fact):
        return fact
    return Fact.from_dict(fact)


def _coerce_query(query: MemoryQuery | Mapping[str, Any] | str) -> MemoryQuery:
    if isinstance(query, MemoryQuery):
        return query
    if isinstance(query, str):
        return MemoryQuery(query_text=query)
    return MemoryQuery.from_dict(query)
