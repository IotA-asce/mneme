from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Iterable

from .models import Episode, Fact, MemoryStatus, SourceType


class MemoryStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.conn.close()

    def apply_migration(self, migration_path: str | Path) -> None:
        sql = Path(migration_path).read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

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
        for entity in episode.participants:
            self.conn.execute(
                "INSERT OR IGNORE INTO episode_entity(episode_id, entity_id, role) VALUES (?, ?, ?)",
                (episode.episode_id, entity, "participant"),
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
        for episode_id in fact.supporting_episode_ids:
            self.conn.execute(
                "INSERT OR IGNORE INTO fact_support(fact_id, episode_id, weight) VALUES (?, ?, 1.0)",
                (fact.fact_id, episode_id),
            )
        self.conn.commit()

    def search_facts(self, text: str, limit: int = 5) -> list[Fact]:
        like = f"%{text.lower()}%"
        rows = self.conn.execute(
            """
            SELECT * FROM fact
            WHERE lower(subject) LIKE ? OR lower(predicate) LIKE ? OR lower(object_json) LIKE ?
            ORDER BY confidence DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        return [
            Fact(
                fact_id=row["fact_id"],
                subject=row["subject"],
                predicate=row["predicate"],
                object_value=json.loads(row["object_json"]),
                confidence=row["confidence"],
                source_type=SourceType(row["source_type"]),
                status=MemoryStatus(row["status"]),
            )
            for row in rows
        ]

    def search_episodes(self, text: str, limit: int = 5) -> list[Episode]:
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
        return [
            Episode(
                episode_id=row["episode_id"],
                start_ts=row["start_ts"],
                end_ts=row["end_ts"],
                summary=row["summary"],
                context=json.loads(row["context_json"]),
                salience=row["salience"],
                confidence=row["confidence"],
            )
            for row in rows
        ]
