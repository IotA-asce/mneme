from __future__ import annotations

from .models import MemoryCandidate, SalienceResult

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


def promotion_decision(score: float, explicit_remember: bool = False) -> str:
    if explicit_remember:
        return "episode_and_semantic_candidate"
    if score < 0.25:
        return "echo_only"
    if score < 0.55:
        return "working_memory_candidate"
    if score < 0.80:
        return "episode"
    return "episode_and_semantic_candidate"


def score_candidate(candidate: MemoryCandidate, weights: dict[str, float] | None = None) -> SalienceResult:
    weights = weights or DEFAULT_WEIGHTS
    features = candidate.features.normalized()
    components: dict[str, float] = {}
    score = 0.0
    for name, weight in weights.items():
        value = getattr(features, name)
        component = value * weight
        components[name] = component
        score += component

    score = max(0.0, min(1.0, score))
    explicit = features.explicit_remember_flag >= 0.9
    decision = promotion_decision(score, explicit_remember=explicit)

    reasons = []
    if explicit:
        reasons.append("explicit remember flag override")
    for name in ("novelty", "task_relevance", "social_relevance", "surprise", "risk", "contradiction"):
        if getattr(features, name) >= 0.7:
            reasons.append(f"high {name}")
    if not reasons:
        reasons.append("weighted salience score")

    return SalienceResult(score=score, decision=decision, reasons=reasons, components=components)
