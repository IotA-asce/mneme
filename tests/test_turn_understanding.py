from android_brain_memory import TurnType, classify_turn


def test_turn_classifier_covers_requested_categories():
    cases = {
        "hello Mneme": TurnType.GREETING,
        "remember that I like tea": TurnType.EXPLICIT_REMEMBER_INSTRUCTION,
        "what do I like?": TurnType.RECALL_QUESTION,
        "that is wrong": TurnType.CORRECTION,
        "but I said something else": TurnType.CONTRADICTION_CHALLENGE,
        "forget that preference": TurnType.FORGET_REQUEST,
        "what are you?": TurnType.IDENTITY_SELF_QUESTION,
        "what can you do?": TurnType.CAPABILITY_QUESTION,
        "what model are you using?": TurnType.DEVICE_STATUS_QUESTION,
        "why did you say that?": TurnType.EXPLANATION_QUESTION,
    }

    for text, expected in cases.items():
        classification = classify_turn(text)
        assert classification.turn_type == expected
        assert classification.to_dict()["turn_type"] == expected.value


def test_turn_classifier_marks_review_and_memory_candidate_flags():
    remember = classify_turn("remember that I like green tea")
    correction = classify_turn("that is wrong")

    assert remember.should_create_memory_candidate is True
    assert remember.requires_review is False
    assert correction.requires_review is True
    assert correction.should_create_memory_candidate is False
