from __future__ import annotations

from dataclasses import dataclass

from .storage import MemoryStore


@dataclass(slots=True)
class ConsolidationReport:
    episodes_examined: int = 0
    summaries_created: int = 0
    facts_created: int = 0
    conflicts_flagged: int = 0
    notes: list[str] | None = None


def consolidate_once(store: MemoryStore, max_episodes: int = 100) -> ConsolidationReport:
    # V1 placeholder: this is intentionally conservative.
    # Future implementation should cluster repeated episodes, create summaries,
    # and stage semantic facts with provenance.
    rows = store.conn.execute(
        "SELECT COUNT(*) AS count FROM episode WHERE status = 'active'"
    ).fetchone()
    count = int(rows["count"] if rows else 0)
    return ConsolidationReport(
        episodes_examined=min(count, max_episodes),
        notes=["consolidation placeholder executed; no mutations performed"],
    )
