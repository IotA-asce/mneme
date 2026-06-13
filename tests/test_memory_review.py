from pathlib import Path

from android_brain_memory import MnemeMemory, MnemeRuntime, RuntimeClock
from android_brain_memory.memory_review import explain_last_response


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def test_runtime_explains_memory_backed_response(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        answer = runtime.process_user_utterance("what do I like?", timestamp=2_000)
        explanation = runtime.process_user_utterance("why did you say that?", timestamp=3_000)

        assert answer.utterances[-1].plan.memory_refs
        assert "because" in explanation.utterances[-1].text.lower()
        assert explanation.utterances[-1].plan.memory_refs == answer.utterances[-1].plan.memory_refs
        assert explanation.snapshot["memory_review"]["last_explanation"]["memory_refs"]
    finally:
        runtime.close()


def test_runtime_records_correction_and_forget_proposals_without_mutating_memory(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        before = runtime.engine.inspect_db()["table_counts"]["fact"]
        correction = runtime.process_user_utterance("that is wrong", timestamp=2_000)
        after = runtime.engine.inspect_db()["table_counts"]["fact"]

        proposal = correction.snapshot["memory_review"]["last_correction_proposal"]
        assert proposal["status"] == "proposed_not_applied"
        assert "not changed memory" in correction.utterances[-1].text.lower()
        assert before == after

        forget = runtime.process_user_utterance("forget that preference", timestamp=3_000)
        assert forget.snapshot["memory_review"]["last_correction_proposal"]["proposal_type"] == "forget_request"
        assert "not purged" in forget.utterances[-1].text.lower()
    finally:
        runtime.close()


def test_runtime_answers_self_capability_status_and_memory_review_questions(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        memories = runtime.process_user_utterance("what do you remember about me?", timestamp=2_000)
        capability = runtime.process_user_utterance("what can you do?", timestamp=3_000)
        status = runtime.process_user_utterance("what model are you using?", timestamp=4_000)
        identity = runtime.process_user_utterance("what are you?", timestamp=5_000)

        assert "green tea" in memories.utterances[-1].text.lower()
        assert memories.utterances[-1].plan.memory_refs
        assert "local brain loop" in capability.utterances[-1].text.lower()
        assert "deterministic fallback" in status.utterances[-1].text.lower()
        assert "mneme" in identity.utterances[-1].text.lower()
    finally:
        runtime.close()


def test_explain_last_response_handles_no_previous_response(tmp_path):
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    try:
        report = explain_last_response(engine.store, None, created_ts=1_000)
        assert report.memory_refs == []
        assert "no previous response" in report.summary.lower()
    finally:
        engine.close()
