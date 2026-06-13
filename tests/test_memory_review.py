from pathlib import Path

import json

from android_brain_memory import Fact, MnemeMemory, MnemeRuntime, RuntimeClock, SourceType
from android_brain_memory.memory_review import apply_memory_review, explain_last_response, reject_memory_review
from android_brain_memory.virtual_head import main as mneme_main


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
        assert proposal["status"] == "proposed"
        assert proposal["review_id"]
        assert "not changed memory" in correction.utterances[-1].text.lower()
        assert before == after
        assert runtime.engine.store.get_memory_review(proposal["review_id"]) is not None

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


def test_apply_correction_review_writes_user_confirmed_fact_and_supersedes_old_fact(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        runtime.process_user_utterance("what do I like?", timestamp=2_000)
        correction = runtime.process_user_utterance("actually I like coffee", timestamp=3_000)
        review_id = correction.snapshot["memory_review"]["last_correction_proposal"]["review_id"]

        applied = apply_memory_review(
            runtime.engine.store,
            review_id,
            reason="test correction approval",
            now_ts=4_000,
        )
        result = applied.action_result

        assert applied.status == "applied"
        assert result["created_fact_ids"]
        fact = runtime.engine.store.get_fact(result["created_fact_ids"][0])
        assert fact is not None
        assert fact.source_type == SourceType.USER_CONFIRMED
        assert fact.object_value["value"] == "coffee"
        counts = runtime.engine.inspect_db()["facts_by_status"]
        assert counts["active"] == 1
        assert counts["superseded"] == 1
    finally:
        runtime.close()


def test_apply_forget_review_suppresses_memory_without_purge(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        runtime.process_user_utterance("what do I like?", timestamp=2_000)
        forget = runtime.process_user_utterance("forget this", timestamp=3_000)
        review_id = forget.snapshot["memory_review"]["last_correction_proposal"]["review_id"]

        applied = apply_memory_review(runtime.engine.store, review_id, reason="test forget", now_ts=4_000)

        assert applied.status == "applied"
        counts = runtime.engine.inspect_db()["facts_by_status"]
        assert counts["suppressed"] == 1
        recall = runtime.process_user_utterance("what do I like?", timestamp=5_000)
        assert not recall.utterances[-1].plan.memory_refs
        assert "green tea" not in recall.utterances[-1].text.lower()
    finally:
        runtime.close()


def test_confirm_then_conflicting_correction_preserves_conflict_for_review(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        runtime.process_user_utterance("what do I like?", timestamp=2_000)
        confirm = runtime.process_user_utterance("confirm this", timestamp=3_000)
        confirm_id = confirm.snapshot["memory_review"]["last_correction_proposal"]["review_id"]
        apply_memory_review(runtime.engine.store, confirm_id, reason="test confirm", now_ts=4_000)

        correction = runtime.process_user_utterance("actually I like coffee", timestamp=5_000)
        correction_id = correction.snapshot["memory_review"]["last_correction_proposal"]["review_id"]
        applied = apply_memory_review(runtime.engine.store, correction_id, reason="test conflict", now_ts=6_000)

        assert applied.status == "applied"
        assert applied.action_result["conflict_reports"]
        counts = runtime.engine.inspect_db()["facts_by_status"]
        assert counts["conflicted"] == 2
        assert runtime.engine.store.get_fact_conflict_reports()
    finally:
        runtime.close()


def test_reject_review_leaves_memory_unchanged(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        runtime.process_user_utterance("what do I like?", timestamp=2_000)
        correction = runtime.process_user_utterance("actually I like coffee", timestamp=3_000)
        before = runtime.engine.inspect_db()["facts_by_status"]
        review_id = correction.snapshot["memory_review"]["last_correction_proposal"]["review_id"]

        rejected = reject_memory_review(runtime.engine.store, review_id, reason="test reject", now_ts=4_000)

        assert rejected.status == "rejected"
        assert runtime.engine.inspect_db()["facts_by_status"] == before
    finally:
        runtime.close()


def test_mneme_review_cli_json_commands(tmp_path, capsys):
    db_path = tmp_path / "memory.sqlite3"
    runtime = MnemeRuntime(
        db_path=db_path,
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.process_user_utterance("remember that I like green tea", timestamp=1_000)
        runtime.process_user_utterance("what do I like?", timestamp=2_000)
        correction = runtime.process_user_utterance("actually I like coffee", timestamp=3_000)
        review_id = correction.snapshot["memory_review"]["last_correction_proposal"]["review_id"]
    finally:
        runtime.close()

    code = mneme_main([
        "--db",
        str(db_path),
        "--migrations",
        str(MIGRATIONS),
        "review",
        "show",
        "--review-id",
        review_id,
        "--json",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["record"]["review_id"] == review_id

    code = mneme_main([
        "--db",
        str(db_path),
        "--migrations",
        str(MIGRATIONS),
        "review",
        "apply",
        "--review-id",
        review_id,
        "--reason",
        "test cli apply",
        "--json",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["record"]["status"] == "applied"


def test_review_explain_cli_returns_memory_ref_explanation(tmp_path, capsys):
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    try:
        fact = Fact(
            fact_id="fact_cli_explain",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
        )
        engine.add_fact(fact, notes="test")
    finally:
        engine.close()

    code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "review",
        "explain",
        "--memory-kind",
        "fact",
        "--memory-id",
        "fact_cli_explain",
        "--json",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["explanations"][0]["memory_id"] == "fact_cli_explain"
