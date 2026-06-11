from __future__ import annotations

from pathlib import Path

import pytest

from android_brain_memory.models import MemoryCandidate, SalienceFeatures, SourceType
from android_brain_memory.salience import (
    PromotionThresholds,
    load_salience_config,
    promotion_decision,
    score_candidate,
)


CONFIG = Path(__file__).resolve().parents[1] / "config" / "memory.yaml"


def candidate_with_features(**features) -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id="test",
        candidate_type="instruction",
        summary="remember this",
        source_type=SourceType.USER_CONFIRMED,
        confidence=1.0,
        features=SalienceFeatures(**features),
    )


@pytest.mark.parametrize(
    ("score", "decision", "threshold_crossed"),
    [
        (0.24, "echo_only", "echo_only"),
        (0.25, "working_memory_candidate", "working_memory_min"),
        (0.55, "episode", "episode_min"),
        (0.80, "episode_and_semantic_candidate", "semantic_candidate_min"),
    ],
)
def test_promotion_threshold_boundaries(score, decision, threshold_crossed):
    result = score_candidate(
        candidate_with_features(novelty=score),
        weights={"novelty": 1.0},
    )

    assert result.score == score
    assert result.decision == decision
    assert result.explanation["threshold_crossed"] == threshold_crossed
    assert result.explanation["weighted_components"]["novelty"] == score


def test_explicit_remember_promotes_to_semantic_candidate():
    result = score_candidate(candidate_with_features(explicit_remember_flag=1.0))

    assert result.decision == "episode_and_semantic_candidate"
    assert result.explanation["override_reason"] == "explicit remember flag override"
    assert "explicit remember flag override" in result.reasons


def test_low_salience_echo_only():
    result = score_candidate(candidate_with_features())

    assert result.decision == "echo_only"
    assert result.explanation["threshold_crossed"] == "echo_only"


def test_config_file_can_drive_default_scoring():
    config = load_salience_config(CONFIG)
    candidate = candidate_with_features(novelty=0.8, task_relevance=0.9, explicit_remember_flag=1.0)

    default_result = score_candidate(candidate)
    config_result = score_candidate(candidate, config_path=CONFIG)

    assert config.weights["novelty"] == 0.22
    assert config.thresholds.echo_only_max == 0.25
    assert config_result.score == default_result.score
    assert config_result.decision == default_result.decision


def test_promotion_thresholds_are_configurable():
    thresholds = PromotionThresholds(
        echo_only_max=0.10,
        working_memory_max=0.20,
        episode_max=0.30,
        semantic_candidate_min=0.30,
    )

    assert promotion_decision(0.25, thresholds=thresholds) == "episode"
    assert score_candidate(
        candidate_with_features(novelty=0.30),
        weights={"novelty": 1.0},
        thresholds=thresholds,
    ).decision == "episode_and_semantic_candidate"


def test_explanation_contains_features_components_threshold_and_override():
    result = score_candidate(
        candidate_with_features(novelty=0.7, task_relevance=0.5),
        weights={"novelty": 0.5, "task_relevance": 0.5},
    )

    explanation = result.explanation
    assert explanation["feature_values"]["novelty"] == 0.7
    assert explanation["weights"]["task_relevance"] == 0.5
    assert explanation["weighted_components"]["novelty"] == 0.35
    assert explanation["thresholds"]["episode_max"] == 0.8
    assert explanation["threshold_crossed"] == "episode_min"
    assert explanation["override_reason"] is None


def test_mutated_feature_values_are_clamped_and_explained_for_scoring():
    features = SalienceFeatures(novelty=1.0, risk=0.0)
    features.novelty = 1.4
    features.risk = -0.2
    candidate = candidate_with_features()
    candidate.features = features

    result = score_candidate(candidate, weights={"novelty": 1.0, "risk": 1.0})

    assert result.score == 1.0
    assert result.explanation["raw_feature_values"]["novelty"] == 1.4
    assert result.explanation["raw_feature_values"]["risk"] == -0.2
    assert result.explanation["feature_values"]["novelty"] == 1.0
    assert result.explanation["feature_values"]["risk"] == 0.0
    assert result.explanation["clamped_features"] == {
        "novelty": {"raw": 1.4, "clamped": 1.0},
        "risk": {"raw": -0.2, "clamped": 0.0},
    }
