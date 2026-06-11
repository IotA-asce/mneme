from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import hashlib
import re
import time
from collections.abc import Mapping
from typing import Any

from .models import Episode, SourceType
from .storage import MemoryStore


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


@dataclass(slots=True)
class ConsolidationOptions:
    max_episodes: int = 100
    min_repetition: int = 3
    close_time_window_s: int = 3600
    update_decay_metadata: bool = True

    def __post_init__(self) -> None:
        self.max_episodes = _positive_int(self.max_episodes, "max_episodes")
        self.min_repetition = _positive_int(self.min_repetition, "min_repetition")
        self.close_time_window_s = _positive_int(
            self.close_time_window_s,
            "close_time_window_s",
        )
        if not isinstance(self.update_decay_metadata, bool):
            raise ValueError("update_decay_metadata must be a boolean")


@dataclass(slots=True)
class ConsolidationReport:
    episodes_examined: int = 0
    groups_considered: int = 0
    groups_summarized: int = 0
    summaries_created: int = 0
    summaries_updated: int = 0
    facts_created: int = 0
    conflicts_flagged: int = 0
    decay_metadata_updates: int = 0
    summary_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _CandidateGroup:
    priority: int
    key: str
    reason: str
    label: str
    episodes: tuple[Episode, ...]


def consolidate_once(
    store: MemoryStore,
    options: ConsolidationOptions | Mapping[str, Any] | None = None,
) -> ConsolidationReport:
    opts = _coerce_options(options)
    episodes = sorted(
        store.get_recent_episodes(limit=opts.max_episodes),
        key=lambda episode: (episode.start_ts, episode.episode_id),
    )
    groups = _candidate_groups(episodes, close_time_window_s=opts.close_time_window_s)
    report = ConsolidationReport(
        episodes_examined=len(episodes),
        groups_considered=len(groups),
    )
    used_episode_ids: set[str] = set()
    now = int(time.time())

    for group in groups:
        available = tuple(
            episode
            for episode in group.episodes
            if episode.episode_id not in used_episode_ids
        )
        if len(available) < opts.min_repetition:
            continue

        summary_id, scope_key = _summary_identity(group.key)
        existing = store.get_memory_summary(summary_id)
        summary_text = _summary_text(group, available)
        confidence = _average_confidence(available)
        episode_ids = [episode.episode_id for episode in available]
        representative = _representative_episode(available)

        record = store.store_memory_summary(
            summary_type="repeated_episode_group",
            scope_key=scope_key,
            summary=summary_text,
            confidence=confidence,
            summary_id=summary_id,
            start_ts=min(episode.start_ts for episode in available),
            end_ts=max(episode.end_ts for episode in available),
            created_ts=now,
            source_type=SourceType.SYSTEM_GENERATED,
            derivation_path=["episode", "consolidation", "summary"],
            supporting_memory_ids=episode_ids,
            notes=f"Deterministic consolidation group: {group.reason}.",
        )
        report.groups_summarized += 1
        if existing is None:
            report.summaries_created += 1
        else:
            report.summaries_updated += 1
        report.summary_ids.append(record.summary_id)

        if opts.update_decay_metadata:
            report.decay_metadata_updates += _update_decay_metadata(
                store,
                available,
                representative,
                record.summary_id,
                now,
            )

        used_episode_ids.update(episode_ids)

    if report.groups_summarized == 0:
        report.notes.append("no repeated episode groups met the minimum repetition threshold")
    else:
        report.notes.append("created deterministic summaries; source episodes were preserved")
    return report


def _coerce_options(
    options: ConsolidationOptions | Mapping[str, Any] | None,
) -> ConsolidationOptions:
    if options is None:
        return ConsolidationOptions()
    if isinstance(options, ConsolidationOptions):
        return options
    if isinstance(options, Mapping):
        return ConsolidationOptions(**dict(options))
    raise ValueError("options must be ConsolidationOptions, a mapping, or None")


def _candidate_groups(
    episodes: list[Episode],
    *,
    close_time_window_s: int,
) -> list[_CandidateGroup]:
    buckets: dict[tuple[int, str, str, str], list[Episode]] = defaultdict(list)
    for episode in episodes:
        for key in _group_keys(episode, close_time_window_s=close_time_window_s):
            buckets[key].append(episode)

    groups = [
        _CandidateGroup(
            priority=priority,
            key=key,
            reason=reason,
            label=label,
            episodes=tuple(sorted(items, key=lambda item: (item.start_ts, item.episode_id))),
        )
        for (priority, key, reason, label), items in buckets.items()
    ]
    return sorted(
        groups,
        key=lambda group: (
            group.priority,
            -len(group.episodes),
            group.key,
        ),
    )


def _group_keys(
    episode: Episode,
    *,
    close_time_window_s: int,
) -> list[tuple[int, str, str, str]]:
    keys: list[tuple[int, str, str, str]] = []
    tags = _episode_tags(episode)
    for tag in tags:
        keys.append((0, f"tag:{tag}", "shared tags", tag))

    participants = sorted(set(episode.participants))
    participant_key = ",".join(participants)
    topic_tokens = _topic_tokens(episode)
    topic_signature = "-".join(topic_tokens[:3])

    if participants and topic_signature:
        keys.append(
            (
                1,
                f"participants:{participant_key}|topic:{topic_signature}",
                "shared participants and similar topic text",
                topic_signature.replace("-", " "),
            )
        )

    for token in topic_tokens[:3]:
        keys.append((2, f"topic:{token}", "similar topic text", token))

    if participants:
        bucket = episode.start_ts // close_time_window_s
        keys.append(
            (
                3,
                f"time:{bucket}|participants:{participant_key}",
                "close time window and shared participants",
                "close time window",
            )
        )
    return keys


def _episode_tags(episode: Episode) -> list[str]:
    values: list[str] = []
    for key in ("tag", "tags"):
        raw = episode.context.get(key)
        if isinstance(raw, str):
            values.append(raw)
        elif isinstance(raw, list):
            values.extend(item for item in raw if isinstance(item, str))
    return sorted({_normalize_label(value) for value in values if value.strip()})


def _topic_tokens(episode: Episode) -> list[str]:
    parts = [episode.summary]
    for key in ("topic", "activity", "event_type"):
        value = episode.context.get(key)
        if isinstance(value, str):
            parts.append(value)
    tokens = {
        token
        for token in TOKEN_PATTERN.findall(" ".join(parts).lower())
        if len(token) > 2 and token not in STOPWORDS
    }
    return sorted(tokens)


def _summary_identity(group_key: str) -> tuple[str, str]:
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:12]
    scope_key = f"episode_group:{digest}"
    return f"summary_{digest}", scope_key


def _summary_text(group: _CandidateGroup, episodes: tuple[Episode, ...]) -> str:
    representative = _representative_episode(episodes)
    participants = sorted({participant for episode in episodes for participant in episode.participants})
    participant_text = ", ".join(participants) if participants else "unspecified participants"
    return (
        f"Observed {len(episodes)} related episodes about {group.label} "
        f"involving {participant_text} between {episodes[0].start_ts} and {episodes[-1].end_ts}. "
        f"Representative episode: {representative.summary}"
    )


def _average_confidence(episodes: tuple[Episode, ...]) -> float:
    return round(sum(episode.confidence for episode in episodes) / len(episodes), 6)


def _representative_episode(episodes: tuple[Episode, ...]) -> Episode:
    return max(
        episodes,
        key=lambda episode: (
            episode.salience,
            episode.confidence,
            episode.end_ts,
            episode.episode_id,
        ),
    )


def _update_decay_metadata(
    store: MemoryStore,
    episodes: tuple[Episode, ...],
    representative: Episode,
    summary_id: str,
    updated_ts: int,
) -> int:
    updates = 0
    for episode in episodes:
        if episode.episode_id == representative.episode_id:
            continue
        store.update_decay_metadata(
            episode.episode_id,
            "episode",
            {
                "policy": "covered_by_summary",
                "accessibility": "downrank_candidate",
                "summary_id": summary_id,
                "representative_episode_id": representative.episode_id,
                "updated_ts": updated_ts,
            },
        )
        updates += 1
    return updates


def _normalize_label(value: str) -> str:
    return "-".join(TOKEN_PATTERN.findall(value.lower()))


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
