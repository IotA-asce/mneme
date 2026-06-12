from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import MemoryStatus, SourceType
from .runtime import EventBus, memory_lifecycle_event
from .storage import MemoryStore, MetaMemoryRecord

DEFAULT_SUPPRESS_AFTER_S = 30 * 24 * 3600
PURGEABLE_MEMORY_KINDS = ("episode", "fact")


@dataclass(slots=True)
class DecayOptions:
    suppress_after_s: int = DEFAULT_SUPPRESS_AFTER_S
    min_retrievals_to_keep: int = 1
    suppress_summarized_episodes: bool = True
    suppress_superseded_facts: bool = True
    max_items: int = 500

    def __post_init__(self) -> None:
        if (
            isinstance(self.suppress_after_s, bool)
            or not isinstance(self.suppress_after_s, int)
            or self.suppress_after_s < 1
        ):
            raise ValueError("suppress_after_s must be a positive integer")
        if (
            isinstance(self.min_retrievals_to_keep, bool)
            or not isinstance(self.min_retrievals_to_keep, int)
            or self.min_retrievals_to_keep < 0
        ):
            raise ValueError("min_retrievals_to_keep must be a non-negative integer")
        if not isinstance(self.suppress_summarized_episodes, bool):
            raise ValueError("suppress_summarized_episodes must be a boolean")
        if not isinstance(self.suppress_superseded_facts, bool):
            raise ValueError("suppress_superseded_facts must be a boolean")
        if isinstance(self.max_items, bool) or not isinstance(self.max_items, int) or self.max_items < 1:
            raise ValueError("max_items must be a positive integer")


@dataclass(slots=True)
class DecayReport:
    episodes_examined: int = 0
    facts_examined: int = 0
    episodes_suppressed: int = 0
    facts_suppressed: int = 0
    suppressed_episode_ids: list[str] = field(default_factory=list)
    suppressed_fact_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episodes_examined": self.episodes_examined,
            "facts_examined": self.facts_examined,
            "episodes_suppressed": self.episodes_suppressed,
            "facts_suppressed": self.facts_suppressed,
            "suppressed_episode_ids": list(self.suppressed_episode_ids),
            "suppressed_fact_ids": list(self.suppressed_fact_ids),
            "notes": list(self.notes),
        }


def run_decay_once(
    store: MemoryStore,
    options: DecayOptions | Mapping[str, Any] | None = None,
    *,
    now_s: int | None = None,
    bus: EventBus | None = None,
    source: str = "memory_decay",
) -> DecayReport:
    """One deterministic suppression pass over decayed memories.

    Suppression is staged forgetting: suppressed memories disappear from
    ordinary retrieval but remain stored with provenance intact and can be
    restored by resetting their status. Nothing is deleted.
    """
    opts = _coerce_options(options)
    now = now_s if now_s is not None else int(time.time())
    report = DecayReport()

    if opts.suppress_summarized_episodes:
        for episode in store.get_recent_episodes(limit=opts.max_items):
            report.episodes_examined += 1
            meta = store.get_meta_memory(episode.episode_id, "episode")
            if meta is None:
                continue
            decay = meta.provenance.get("decay")
            if not isinstance(decay, Mapping) or decay.get("policy") != "covered_by_summary":
                continue
            if meta.retrieval_count >= opts.min_retrievals_to_keep:
                continue
            reference_ts = (
                meta.last_retrieved_ts
                if meta.last_retrieved_ts is not None
                else episode.end_ts
            )
            if now - reference_ts <= opts.suppress_after_s:
                continue
            store.set_episode_status(episode.episode_id, MemoryStatus.SUPPRESSED)
            report.episodes_suppressed += 1
            report.suppressed_episode_ids.append(episode.episode_id)
        report.suppressed_episode_ids.sort()

    if opts.suppress_superseded_facts:
        superseded = store.search_facts_structured(
            status=MemoryStatus.SUPERSEDED,
            limit=opts.max_items,
        )
        for fact in superseded:
            report.facts_examined += 1
            if fact.source_type == SourceType.USER_CONFIRMED:
                report.notes.append(
                    f"kept user-confirmed fact {fact.fact_id} despite superseded status"
                )
                continue
            meta = store.get_meta_memory(fact.fact_id, "fact")
            reference_ts = _fact_reference_ts(store, fact.fact_id, meta)
            if reference_ts is None or now - reference_ts <= opts.suppress_after_s:
                continue
            store.set_fact_status(fact.fact_id, MemoryStatus.SUPPRESSED)
            report.facts_suppressed += 1
            report.suppressed_fact_ids.append(fact.fact_id)
        report.suppressed_fact_ids.sort()

    if not report.episodes_suppressed and not report.facts_suppressed:
        report.notes.append("no memories met the suppression criteria")

    if bus is not None:
        bus.publish(
            memory_lifecycle_event(
                source=source,
                lifecycle_stage="decay",
                timestamp=now * 1000,
                payload=report.to_dict(),
            )
        )
    return report


def purge_memory(
    store: MemoryStore,
    memory_id: str,
    memory_kind: str,
    *,
    reason: str,
    force: bool = False,
    now_s: int | None = None,
) -> None:
    """Explicit purge: a provenance-preserving tombstone, never a deletion.

    Sets the row status to purged and records the reason in meta-memory.
    User-confirmed facts require force=True so they are never purged casually.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason must be a non-empty string")
    if memory_kind not in PURGEABLE_MEMORY_KINDS:
        allowed = ", ".join(PURGEABLE_MEMORY_KINDS)
        raise ValueError(f"memory_kind must be one of: {allowed}")
    now = now_s if now_s is not None else int(time.time())

    if memory_kind == "episode":
        if store.get_episode(memory_id) is None:
            raise KeyError(f"episode not found: {memory_id}")
        source_type = SourceType.SYSTEM_GENERATED
        store.set_episode_status(memory_id, MemoryStatus.PURGED)
    else:
        fact = store.get_fact(memory_id)
        if fact is None:
            raise KeyError(f"fact not found: {memory_id}")
        if fact.source_type == SourceType.USER_CONFIRMED and not force:
            raise ValueError(
                "purging a user-confirmed fact requires force=True and an explicit reason"
            )
        source_type = fact.source_type
        store.set_fact_status(memory_id, MemoryStatus.PURGED)

    purge_note = {"reason": reason, "purged_ts": now, "forced": force}
    meta = store.get_meta_memory(memory_id, memory_kind)
    if meta is None:
        store.write_meta_memory(
            MetaMemoryRecord(
                memory_id=memory_id,
                memory_kind=memory_kind,
                source_type=source_type,
                provenance={"purge": purge_note},
            )
        )
    else:
        provenance = dict(meta.provenance)
        provenance["purge"] = purge_note
        store.update_meta_memory(memory_id, memory_kind, provenance=provenance)


def _fact_reference_ts(
    store: MemoryStore,
    fact_id: str,
    meta: MetaMemoryRecord | None,
) -> int | None:
    if meta is not None and meta.last_retrieved_ts is not None:
        return meta.last_retrieved_ts
    row = store.conn.execute(
        "SELECT first_seen_ts, last_confirmed_ts FROM fact WHERE fact_id = ?",
        (fact_id,),
    ).fetchone()
    if row is None:
        return None
    if row["last_confirmed_ts"] is not None:
        return row["last_confirmed_ts"]
    return row["first_seen_ts"]


def _coerce_options(options: DecayOptions | Mapping[str, Any] | None) -> DecayOptions:
    if options is None:
        return DecayOptions()
    if isinstance(options, DecayOptions):
        return options
    if isinstance(options, Mapping):
        return DecayOptions(**dict(options))
    raise ValueError("options must be DecayOptions, a mapping, or None")
