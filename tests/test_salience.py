from android_brain_memory.models import MemoryCandidate, SalienceFeatures, SourceType
from android_brain_memory.salience import score_candidate


def test_explicit_remember_promotes_to_semantic_candidate():
    candidate = MemoryCandidate(
        candidate_id="test",
        candidate_type="instruction",
        summary="remember this",
        source_type=SourceType.USER_CONFIRMED,
        confidence=1.0,
        features=SalienceFeatures(explicit_remember_flag=1.0),
    )
    result = score_candidate(candidate)
    assert result.decision == "episode_and_semantic_candidate"


def test_low_salience_echo_only():
    candidate = MemoryCandidate(
        candidate_id="test_low",
        candidate_type="noise",
        summary="background noise",
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.5,
        features=SalienceFeatures(),
    )
    result = score_candidate(candidate)
    assert result.decision == "echo_only"
