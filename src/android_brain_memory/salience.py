from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import MemoryCandidate, SalienceResult, validate_salience

DEFAULT_WEIGHTS = {
    "novelty": 0.22,
    "task_relevance": 0.18,
    "social_relevance": 0.18,
    "surprise": 0.14,
    "risk": 0.12,
    "contradiction": 0.08,
    "repetition_signal": 0.05,
    "explicit_remember_flag": 0.03,
}

DEFAULT_THRESHOLDS = {
    "echo_only_max": 0.25,
    "working_memory_max": 0.55,
    "episode_max": 0.80,
    "semantic_candidate_min": 0.80,
}

DEFAULT_CONFIG_PATH = Path("config/memory.yaml")


@dataclass(frozen=True, slots=True)
class PromotionThresholds:
    echo_only_max: float = 0.25
    working_memory_max: float = 0.55
    episode_max: float = 0.80
    semantic_candidate_min: float = 0.80

    def __post_init__(self) -> None:
        object.__setattr__(self, "echo_only_max", validate_salience(self.echo_only_max, "echo_only_max"))
        object.__setattr__(
            self,
            "working_memory_max",
            validate_salience(self.working_memory_max, "working_memory_max"),
        )
        object.__setattr__(self, "episode_max", validate_salience(self.episode_max, "episode_max"))
        object.__setattr__(
            self,
            "semantic_candidate_min",
            validate_salience(self.semantic_candidate_min, "semantic_candidate_min"),
        )
        if not self.echo_only_max <= self.working_memory_max <= self.episode_max:
            raise ValueError("promotion thresholds must be ordered echo <= working <= episode")
        if self.semantic_candidate_min != self.episode_max:
            raise ValueError("semantic_candidate_min must match episode_max in V1")

    def to_dict(self) -> dict[str, float]:
        return {
            "echo_only_max": self.echo_only_max,
            "working_memory_max": self.working_memory_max,
            "episode_max": self.episode_max,
            "semantic_candidate_min": self.semantic_candidate_min,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "PromotionThresholds":
        data = data or {}
        return cls(
            echo_only_max=data.get("echo_only_max", DEFAULT_THRESHOLDS["echo_only_max"]),
            working_memory_max=data.get("working_memory_max", DEFAULT_THRESHOLDS["working_memory_max"]),
            episode_max=data.get("episode_max", DEFAULT_THRESHOLDS["episode_max"]),
            semantic_candidate_min=data.get(
                "semantic_candidate_min",
                data.get("episode_max", DEFAULT_THRESHOLDS["semantic_candidate_min"]),
            ),
        )


@dataclass(frozen=True, slots=True)
class SalienceScoringConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    thresholds: PromotionThresholds = field(default_factory=PromotionThresholds)
    explicit_remember_override: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "weights", validate_weights(self.weights))
        if not isinstance(self.thresholds, PromotionThresholds):
            object.__setattr__(self, "thresholds", PromotionThresholds.from_mapping(self.thresholds))
        if not isinstance(self.explicit_remember_override, bool):
            raise ValueError("explicit_remember_override must be a boolean")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SalienceScoringConfig":
        salience = data.get("salience", data)
        if not isinstance(salience, Mapping):
            raise ValueError("salience config must be a mapping")
        return cls(
            weights=dict(salience.get("weights", DEFAULT_WEIGHTS)),
            thresholds=PromotionThresholds.from_mapping(salience.get("thresholds", DEFAULT_THRESHOLDS)),
            explicit_remember_override=salience.get("explicit_remember_override", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "weights": dict(self.weights),
            "thresholds": self.thresholds.to_dict(),
            "explicit_remember_override": self.explicit_remember_override,
        }


def validate_weights(weights: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(weights, Mapping):
        raise ValueError("weights must be a mapping")
    validated: dict[str, float] = {}
    for name in DEFAULT_WEIGHTS:
        value = weights.get(name, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"weight {name} must be a non-negative finite number")
        normalized = float(value)
        if not math.isfinite(normalized) or normalized < 0.0:
            raise ValueError(f"weight {name} must be a non-negative finite number")
        validated[name] = normalized
    unknown = sorted(set(weights) - set(DEFAULT_WEIGHTS))
    if unknown:
        raise ValueError(f"unknown salience weight(s): {', '.join(unknown)}")
    return validated


def load_salience_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> SalienceScoringConfig:
    path = Path(config_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, Mapping):
        raise ValueError(f"salience config file must contain a mapping: {path}")
    return SalienceScoringConfig.from_mapping(data)


def promotion_decision(
    score: float,
    explicit_remember: bool = False,
    thresholds: PromotionThresholds | Mapping[str, Any] | None = None,
    explicit_remember_override: bool = True,
) -> str:
    thresholds = _coerce_thresholds(thresholds)
    if explicit_remember and explicit_remember_override:
        return "episode_and_semantic_candidate"
    if score < thresholds.echo_only_max:
        return "echo_only"
    if score < thresholds.working_memory_max:
        return "working_memory_candidate"
    if score < thresholds.episode_max:
        return "episode"
    return "episode_and_semantic_candidate"


def score_candidate(
    candidate: MemoryCandidate,
    weights: dict[str, float] | None = None,
    thresholds: PromotionThresholds | Mapping[str, Any] | None = None,
    config: SalienceScoringConfig | None = None,
    config_path: str | Path | None = None,
) -> SalienceResult:
    scoring_config = _resolve_config(weights, thresholds, config, config_path)
    feature_values, raw_feature_values, clamped_features = _feature_values(candidate)

    components: dict[str, float] = {}
    score = 0.0
    for name, weight in scoring_config.weights.items():
        component = feature_values[name] * weight
        components[name] = component
        score += component

    raw_score = score
    score = max(0.0, min(1.0, score))
    explicit = feature_values["explicit_remember_flag"] >= 0.9
    threshold_crossed = threshold_for_score(score, scoring_config.thresholds)
    override_reason = (
        "explicit remember flag override"
        if explicit and scoring_config.explicit_remember_override
        else None
    )
    decision = promotion_decision(
        score,
        explicit_remember=explicit,
        thresholds=scoring_config.thresholds,
        explicit_remember_override=scoring_config.explicit_remember_override,
    )

    reasons = []
    if override_reason:
        reasons.append(override_reason)
    for name in ("novelty", "task_relevance", "social_relevance", "surprise", "risk", "contradiction"):
        if feature_values[name] >= 0.7:
            reasons.append(f"high {name}")
    if clamped_features:
        reasons.append("feature values clamped for scoring")
    if not reasons:
        reasons.append("weighted salience score")

    explanation = {
        "feature_values": feature_values,
        "raw_feature_values": raw_feature_values,
        "weights": dict(scoring_config.weights),
        "weighted_components": dict(components),
        "raw_score": raw_score,
        "score": score,
        "thresholds": scoring_config.thresholds.to_dict(),
        "threshold_crossed": threshold_crossed,
        "decision": decision,
        "override_reason": override_reason,
        "clamped_features": clamped_features,
    }

    return SalienceResult(
        score=score,
        decision=decision,
        reasons=reasons,
        components=components,
        explanation=explanation,
    )


def threshold_for_score(score: float, thresholds: PromotionThresholds | Mapping[str, Any] | None = None) -> str:
    thresholds = _coerce_thresholds(thresholds)
    if score < thresholds.echo_only_max:
        return "echo_only"
    if score < thresholds.working_memory_max:
        return "working_memory_min"
    if score < thresholds.episode_max:
        return "episode_min"
    return "semantic_candidate_min"


def _resolve_config(
    weights: dict[str, float] | None,
    thresholds: PromotionThresholds | Mapping[str, Any] | None,
    config: SalienceScoringConfig | None,
    config_path: str | Path | None,
) -> SalienceScoringConfig:
    if config is not None and config_path is not None:
        raise ValueError("pass either config or config_path, not both")
    if config_path is not None:
        config = load_salience_config(config_path)
    if config is None:
        config = SalienceScoringConfig()
    if weights is not None or thresholds is not None:
        config = SalienceScoringConfig(
            weights=weights if weights is not None else config.weights,
            thresholds=thresholds if thresholds is not None else config.thresholds,
            explicit_remember_override=config.explicit_remember_override,
        )
    return config


def _coerce_thresholds(thresholds: PromotionThresholds | Mapping[str, Any] | None) -> PromotionThresholds:
    if thresholds is None:
        return PromotionThresholds()
    if isinstance(thresholds, PromotionThresholds):
        return thresholds
    return PromotionThresholds.from_mapping(thresholds)


def _feature_values(candidate: MemoryCandidate) -> tuple[dict[str, float], dict[str, float], dict[str, dict[str, float]]]:
    feature_values: dict[str, float] = {}
    raw_feature_values: dict[str, float] = {}
    clamped_features: dict[str, dict[str, float]] = {}
    for name in DEFAULT_WEIGHTS:
        raw_value = getattr(candidate.features, name)
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(raw_value):
            raise ValueError(f"{name} must be a finite numeric feature value")
        raw = float(raw_value)
        clamped = max(0.0, min(1.0, raw))
        raw_feature_values[name] = raw
        feature_values[name] = clamped
        if raw != clamped:
            clamped_features[name] = {"raw": raw, "clamped": clamped}
    return feature_values, raw_feature_values, clamped_features
