from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
import time
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .models import (
    Episode,
    Fact,
    MemoryStatus,
    SourceType,
    parse_memory_status,
    parse_source_type,
    validate_salience,
    validate_timestamp,
)


@dataclass(slots=True)
class MigrationRecord:
    migration_id: str
    filename: str
    checksum_sha256: str
    applied_ts: int


@dataclass(slots=True)
class MetaMemoryRecord:
    memory_id: str
    memory_kind: str
    source_type: SourceType
    provenance: dict[str, Any]
    last_retrieved_ts: int | None = None
    retrieval_count: int = 0
    contradiction_score: float = 0.0
    speakability: str = "normal"

    def __post_init__(self) -> None:
        self.memory_id = _required_text(self.memory_id, "memory_id")
        self.memory_kind = _required_text(self.memory_kind, "memory_kind")
        self.source_type = parse_source_type(self.source_type)
        self.provenance = _json_mapping(self.provenance, "provenance")
        if self.last_retrieved_ts is not None:
            self.last_retrieved_ts = validate_timestamp(self.last_retrieved_ts, "last_retrieved_ts")
        self.retrieval_count = _non_negative_int(self.retrieval_count, "retrieval_count")
        self.contradiction_score = validate_salience(self.contradiction_score, "contradiction_score")
        self.speakability = _required_text(self.speakability, "speakability")


@dataclass(slots=True)
class WorkingContextSnapshot:
    snapshot_id: str
    created_ts: int
    context: dict[str, Any]

    def __post_init__(self) -> None:
        self.snapshot_id = _required_text(self.snapshot_id, "snapshot_id")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.context = _json_mapping(self.context, "context")


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _string_list(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must be a list of strings")
    return items


class MemoryStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.conn.close()

    def _ensure_migration_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migration (
              migration_id TEXT PRIMARY KEY,
              filename TEXT NOT NULL,
              checksum_sha256 TEXT NOT NULL,
              applied_ts INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    def get_applied_migrations(self) -> list[MigrationRecord]:
        self._ensure_migration_table()
        rows = self.conn.execute(
            """
            SELECT migration_id, filename, checksum_sha256, applied_ts
            FROM schema_migration
            ORDER BY migration_id
            """
        ).fetchall()
        return [
            MigrationRecord(
                migration_id=row["migration_id"],
                filename=row["filename"],
                checksum_sha256=row["checksum_sha256"],
                applied_ts=row["applied_ts"],
            )
            for row in rows
        ]

    def apply_migration(self, migration_path: str | Path) -> MigrationRecord | None:
        self._ensure_migration_table()
        path = Path(migration_path)
        sql = path.read_text(encoding="utf-8")
        migration_id = path.stem
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        existing = self.conn.execute(
            """
            SELECT migration_id, filename, checksum_sha256, applied_ts
            FROM schema_migration
            WHERE migration_id = ?
            """,
            (migration_id,),
        ).fetchone()
        if existing:
            if existing["checksum_sha256"] != checksum:
                raise RuntimeError(
                    f"migration {migration_id} was already applied with a different checksum"
                )
            return None

        self.conn.executescript(sql)
        applied_ts = int(time.time())
        self.conn.execute(
            """
            INSERT INTO schema_migration(migration_id, filename, checksum_sha256, applied_ts)
            VALUES (?, ?, ?, ?)
            """,
            (migration_id, path.name, checksum, applied_ts),
        )
        self.conn.commit()
        return MigrationRecord(
            migration_id=migration_id,
            filename=path.name,
            checksum_sha256=checksum,
            applied_ts=applied_ts,
        )

    def run_migrations(self, migrations_dir: str | Path) -> list[MigrationRecord]:
        applied = []
        for migration_path in sorted(Path(migrations_dir).glob("*.sql")):
            record = self.apply_migration(migration_path)
            if record is not None:
                applied.append(record)
        return applied

    def store_raw_trace(
        self,
        summary: str,
        payload: dict,
        source_type: SourceType,
        confidence: float,
        salience: float,
        source_id: str | None = None,
    ) -> str:
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        now = int(time.time())
        self.conn.execute(
            """
            INSERT INTO raw_trace(trace_id, created_ts, source_type, source_id, summary, payload_json, confidence, salience)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (trace_id, now, source_type.value, source_id, summary, json.dumps(payload), confidence, salience),
        )
        self.conn.commit()
        return trace_id

    def store_episode(self, episode: Episode) -> None:
        now = int(time.time())
        self.conn.execute(
            """
            INSERT OR REPLACE INTO episode(episode_id, start_ts, end_ts, context_json, summary, salience, confidence, status, created_ts, updated_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                episode.episode_id,
                episode.start_ts,
                episode.end_ts,
                json.dumps(episode.context),
                episode.summary,
                episode.salience,
                episode.confidence,
                now,
                now,
            ),
        )
        self.conn.execute("DELETE FROM episode_entity WHERE episode_id = ?", (episode.episode_id,))
        for entity in episode.participants:
            self.conn.execute(
                "INSERT OR IGNORE INTO episode_entity(episode_id, entity_id, role) VALUES (?, ?, ?)",
                (episode.episode_id, entity, "participant"),
            )
        for entity in episode.objects:
            self.conn.execute(
                "INSERT OR IGNORE INTO episode_entity(episode_id, entity_id, role) VALUES (?, ?, ?)",
                (episode.episode_id, entity, "object"),
            )
        self.conn.commit()

    def upsert_fact(self, fact: Fact) -> None:
        now = int(time.time())
        last_confirmed = now if fact.source_type == SourceType.USER_CONFIRMED else None
        self.conn.execute(
            """
            INSERT OR REPLACE INTO fact(fact_id, subject, predicate, object_json, confidence, source_type, status, first_seen_ts, last_confirmed_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT first_seen_ts FROM fact WHERE fact_id = ?), ?), ?)
            """,
            (
                fact.fact_id,
                fact.subject,
                fact.predicate,
                json.dumps(fact.object_value),
                fact.confidence,
                fact.source_type.value,
                fact.status.value,
                fact.fact_id,
                now,
                last_confirmed,
            ),
        )
        if self._table_exists("fact_tag"):
            self.conn.execute("DELETE FROM fact_tag WHERE fact_id = ?", (fact.fact_id,))
            for tag in fact.tags:
                self.conn.execute(
                    "INSERT OR IGNORE INTO fact_tag(fact_id, tag) VALUES (?, ?)",
                    (fact.fact_id, tag),
                )
        self.conn.execute("DELETE FROM fact_support WHERE fact_id = ?", (fact.fact_id,))
        for episode_id in fact.supporting_episode_ids:
            self.conn.execute(
                "INSERT OR IGNORE INTO fact_support(fact_id, episode_id, weight) VALUES (?, ?, 1.0)",
                (fact.fact_id, episode_id),
            )
        self.conn.commit()

    def write_meta_memory(self, record: MetaMemoryRecord) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO meta_memory(
                memory_id,
                memory_kind,
                source_type,
                provenance_json,
                last_retrieved_ts,
                retrieval_count,
                contradiction_score,
                speakability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.memory_id,
                record.memory_kind,
                record.source_type.value,
                json.dumps(record.provenance),
                record.last_retrieved_ts,
                record.retrieval_count,
                record.contradiction_score,
                record.speakability,
            ),
        )
        self.conn.commit()

    def get_meta_memory(self, memory_id: str, memory_kind: str) -> MetaMemoryRecord | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM meta_memory
            WHERE memory_id = ? AND memory_kind = ?
            """,
            (memory_id, memory_kind),
        ).fetchone()
        return self._meta_memory_from_row(row) if row else None

    def update_meta_memory(
        self,
        memory_id: str,
        memory_kind: str,
        *,
        source_type: SourceType | str | None = None,
        provenance: dict[str, Any] | None = None,
        last_retrieved_ts: int | None = None,
        retrieval_count: int | None = None,
        contradiction_score: float | None = None,
        speakability: str | None = None,
    ) -> MetaMemoryRecord:
        existing = self.get_meta_memory(memory_id, memory_kind)
        if existing is None:
            raise KeyError(f"meta-memory record not found: {memory_kind}/{memory_id}")
        updated = MetaMemoryRecord(
            memory_id=existing.memory_id,
            memory_kind=existing.memory_kind,
            source_type=source_type if source_type is not None else existing.source_type,
            provenance=provenance if provenance is not None else existing.provenance,
            last_retrieved_ts=(
                last_retrieved_ts if last_retrieved_ts is not None else existing.last_retrieved_ts
            ),
            retrieval_count=(
                retrieval_count if retrieval_count is not None else existing.retrieval_count
            ),
            contradiction_score=(
                contradiction_score
                if contradiction_score is not None
                else existing.contradiction_score
            ),
            speakability=speakability if speakability is not None else existing.speakability,
        )
        self.write_meta_memory(updated)
        return updated

    def store_working_context_snapshot(
        self,
        context: dict[str, Any],
        *,
        snapshot_id: str | None = None,
        created_ts: int | None = None,
    ) -> WorkingContextSnapshot:
        snapshot = WorkingContextSnapshot(
            snapshot_id=snapshot_id or f"ctx_{uuid.uuid4().hex[:12]}",
            created_ts=created_ts if created_ts is not None else int(time.time()),
            context=context,
        )
        self.conn.execute(
            """
            INSERT INTO working_context_snapshot(snapshot_id, created_ts, context_json)
            VALUES (?, ?, ?)
            """,
            (snapshot.snapshot_id, snapshot.created_ts, json.dumps(snapshot.context)),
        )
        self.conn.commit()
        return snapshot

    def get_recent_working_context_snapshots(self, limit: int = 5) -> list[WorkingContextSnapshot]:
        limit = _positive_int(limit, "limit")
        rows = self.conn.execute(
            """
            SELECT snapshot_id, created_ts, context_json
            FROM working_context_snapshot
            ORDER BY created_ts DESC, snapshot_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._working_context_snapshot_from_row(row) for row in rows]

    def get_episode(self, episode_id: str) -> Episode | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM episode
            WHERE episode_id = ?
            """,
            (episode_id,),
        ).fetchone()
        return self._episode_from_row(row) if row else None

    def get_fact(self, fact_id: str) -> Fact | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM fact
            WHERE fact_id = ?
            """,
            (fact_id,),
        ).fetchone()
        return self._fact_from_row(row) if row else None

    def search_facts(self, text: str, limit: int = 5) -> list[Fact]:
        return self.search_facts_structured(query_text=text, limit=limit)

    def search_facts_structured(
        self,
        *,
        query_text: str = "",
        subject: str = "",
        predicate: str = "",
        object_text: str = "",
        source_type: SourceType | str | None = None,
        status: MemoryStatus | str | None = MemoryStatus.ACTIVE,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> list[Fact]:
        limit = _positive_int(limit, "limit")
        source = parse_source_type(source_type, "source_type") if source_type is not None else None
        status_filter = parse_memory_status(status, "status") if status is not None else None
        tag_filters = _string_list(tags or [], "tags")

        where_clauses = []
        params: list[Any] = []

        if query_text.strip():
            like = f"%{query_text.lower()}%"
            where_clauses.append("(lower(subject) LIKE ? OR lower(predicate) LIKE ? OR lower(object_json) LIKE ?)")
            params.extend([like, like, like])
        if subject.strip():
            where_clauses.append("lower(subject) LIKE ?")
            params.append(f"%{subject.lower()}%")
        if predicate.strip():
            where_clauses.append("lower(predicate) LIKE ?")
            params.append(f"%{predicate.lower()}%")
        if object_text.strip():
            where_clauses.append("lower(object_json) LIKE ?")
            params.append(f"%{object_text.lower()}%")
        if source is not None:
            where_clauses.append("source_type = ?")
            params.append(source.value)
        if status_filter is not None:
            where_clauses.append("status = ?")
            params.append(status_filter.value)
        if tag_filters:
            if not self._table_exists("fact_tag"):
                return []
            for tag in tag_filters:
                where_clauses.append(
                    """
                    EXISTS (
                      SELECT 1
                      FROM fact_tag
                      WHERE fact_tag.fact_id = fact.fact_id
                        AND lower(fact_tag.tag) = ?
                    )
                    """
                )
                params.append(tag.lower())

        where_sql = " AND ".join(where_clauses) if where_clauses else "1 = 1"
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM fact
            WHERE {where_sql}
            ORDER BY
              CASE source_type
                WHEN 'user_confirmed' THEN 0
                WHEN 'imported' THEN 1
                WHEN 'system_generated' THEN 2
                WHEN 'executive_generated' THEN 3
                WHEN 'sensor_observed' THEN 4
                WHEN 'model_inferred' THEN 5
                ELSE 6
              END,
              confidence DESC,
              COALESCE(last_confirmed_ts, first_seen_ts) DESC,
              fact_id ASC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [self._fact_from_row(row) for row in rows]

    def search_episodes(self, text: str, limit: int = 5) -> list[Episode]:
        limit = _positive_int(limit, "limit")
        like = f"%{text.lower()}%"
        rows = self.conn.execute(
            """
            SELECT * FROM episode
            WHERE lower(summary) LIKE ? OR lower(context_json) LIKE ?
            ORDER BY salience DESC, start_ts DESC
            LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        return [self._episode_from_row(row) for row in rows]

    def _episode_from_row(self, row: sqlite3.Row) -> Episode:
        entity_rows = self.conn.execute(
            """
            SELECT entity_id, role
            FROM episode_entity
            WHERE episode_id = ?
            ORDER BY entity_id
            """,
            (row["episode_id"],),
        ).fetchall()
        participants = [
            entity["entity_id"]
            for entity in entity_rows
            if entity["role"] == "participant"
        ]
        objects = [
            entity["entity_id"]
            for entity in entity_rows
            if entity["role"] == "object"
        ]
        return Episode(
            episode_id=row["episode_id"],
            start_ts=row["start_ts"],
            end_ts=row["end_ts"],
            summary=row["summary"],
            context=json.loads(row["context_json"]),
            salience=row["salience"],
            confidence=row["confidence"],
            participants=participants,
            objects=objects,
        )

    def _fact_from_row(self, row: sqlite3.Row) -> Fact:
        support_rows = self.conn.execute(
            """
            SELECT episode_id
            FROM fact_support
            WHERE fact_id = ?
            ORDER BY episode_id
            """,
            (row["fact_id"],),
        ).fetchall()
        tag_rows = []
        if self._table_exists("fact_tag"):
            tag_rows = self.conn.execute(
                """
                SELECT tag
                FROM fact_tag
                WHERE fact_id = ?
                ORDER BY tag
                """,
                (row["fact_id"],),
            ).fetchall()
        return Fact(
            fact_id=row["fact_id"],
            subject=row["subject"],
            predicate=row["predicate"],
            object_value=json.loads(row["object_json"]),
            confidence=row["confidence"],
            source_type=SourceType(row["source_type"]),
            status=MemoryStatus(row["status"]),
            tags=[tag["tag"] for tag in tag_rows],
            supporting_episode_ids=[support["episode_id"] for support in support_rows],
        )

    def _table_exists(self, table_name: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _meta_memory_from_row(row: sqlite3.Row) -> MetaMemoryRecord:
        return MetaMemoryRecord(
            memory_id=row["memory_id"],
            memory_kind=row["memory_kind"],
            source_type=SourceType(row["source_type"]),
            provenance=json.loads(row["provenance_json"]),
            last_retrieved_ts=row["last_retrieved_ts"],
            retrieval_count=row["retrieval_count"],
            contradiction_score=row["contradiction_score"],
            speakability=row["speakability"],
        )

    @staticmethod
    def _working_context_snapshot_from_row(row: sqlite3.Row) -> WorkingContextSnapshot:
        return WorkingContextSnapshot(
            snapshot_id=row["snapshot_id"],
            created_ts=row["created_ts"],
            context=json.loads(row["context_json"]),
        )
