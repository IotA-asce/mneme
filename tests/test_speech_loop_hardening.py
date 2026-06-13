from __future__ import annotations

import json
from pathlib import Path

from android_brain_memory import (
    EvaluationLogger,
    FixtureSpeechOutputBackend,
    FixtureSpeechRecognitionBackend,
    MnemeRuntime,
    RuntimeClock,
    SpeechLoopDiagnostics,
    run_speech_soak,
    run_speech_soak_suite,
)
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "speech"


def test_speech_loop_diagnostics_records_normal_turn(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend([
            {"speaker": "user", "transcript": "hello Mneme", "confidence": 0.9}
        ]),
        speech_output_backend=FixtureSpeechOutputBackend(),
    )
    try:
        runtime.start()
        result = runtime.tick(advance_ms=1_000)
        speech_loop = result.snapshot["speech_loop"]

        assert result.utterances
        assert speech_loop["latest_capture_report"]["status"] == "transcribed"
        assert speech_loop["counters"]["responses_generated"] == 1
        assert speech_loop["counters"]["tts_completed"] == 1
        assert speech_loop["latest_asr_latency_ms"] >= 0
        assert speech_loop["latest_response_latency_ms"] >= 0
        assert speech_loop["latest_tts_latency_ms"] >= 0
    finally:
        runtime.close()


def test_duplicate_live_transcript_is_not_spoken_twice(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend([
            {"speaker": "user", "transcript": "hello Mneme"},
            {"speaker": "user", "transcript": "hello Mneme"},
        ]),
        speech_output_backend=FixtureSpeechOutputBackend(),
    )
    try:
        runtime.start()
        first = runtime.tick(advance_ms=1_000)
        second = runtime.tick(advance_ms=1_000)
        speech_loop = second.snapshot["speech_loop"]

        assert len(first.utterances) == 1
        assert second.utterances == []
        assert speech_loop["counters"]["responses_generated"] == 1
        assert speech_loop["counters"]["duplicate_suppressions"] == 1
        assert speech_loop["latest_turn"]["suppressed"] is True
    finally:
        runtime.close()


def test_no_microphone_and_no_speech_are_structured_statuses(tmp_path):
    no_mic = MnemeRuntime(
        db_path=tmp_path / "no_mic.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        fake_devices=[],
        live_speech_backend=FixtureSpeechRecognitionBackend([]),
    )
    try:
        no_mic.start()
        no_mic_result = no_mic.tick(advance_ms=1_000)
        assert no_mic_result.snapshot["speech_loop"]["latest_capture_report"]["status"] == "no_microphone"
        assert no_mic_result.snapshot["speech_loop"]["current_state"] == "degraded"
    finally:
        no_mic.close()

    no_speech = MnemeRuntime(
        db_path=tmp_path / "no_speech.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend([
            {"status": "no_speech"}
        ]),
    )
    try:
        no_speech.start()
        no_speech_result = no_speech.tick(advance_ms=1_000)
        speech_loop = no_speech_result.snapshot["speech_loop"]
        assert speech_loop["latest_capture_report"]["status"] == "no_speech"
        assert speech_loop["counters"]["no_speech"] == 1
        assert no_speech_result.utterances == []
    finally:
        no_speech.close()


def test_asr_and_tts_failures_recover_to_structured_degraded_state(tmp_path):
    asr_runtime = MnemeRuntime(
        db_path=tmp_path / "asr.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend([
            {"status": "error", "error": "asr timeout"}
        ]),
    )
    try:
        asr_runtime.start()
        asr_result = asr_runtime.tick(advance_ms=1_000)
        speech_loop = asr_result.snapshot["speech_loop"]
        assert speech_loop["latest_capture_report"]["status"] == "capture_error"
        assert speech_loop["counters"]["capture_errors"] == 1
        assert "capture_error" in speech_loop["latest_failure_reason"]
    finally:
        asr_runtime.close()

    tts_runtime = MnemeRuntime(
        db_path=tmp_path / "tts.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend([
            {"speaker": "user", "transcript": "hello Mneme"}
        ]),
        speech_output_backend=FixtureSpeechOutputBackend(fail_on_calls=[1]),
    )
    try:
        tts_runtime.start()
        tts_result = tts_runtime.tick(advance_ms=1_000)
        speech_loop = tts_result.snapshot["speech_loop"]
        assert len(tts_result.utterances) == 1
        assert speech_loop["counters"]["tts_failures"] == 1
        assert speech_loop["current_state"] == "degraded"
        assert "tts_failed" in speech_loop["latest_failure_reason"]
    finally:
        tts_runtime.close()


def test_barge_in_and_stuck_speaking_are_counted(tmp_path):
    barge_report = run_speech_soak(FIXTURES / "barge_in.yaml", migrations_dir=MIGRATIONS)
    assert barge_report.total_score == 1.0
    assert barge_report.final_snapshot["speech_loop"]["counters"]["barge_ins"] == 1

    stuck_report = run_speech_soak(FIXTURES / "stuck_speaking.yaml", migrations_dir=MIGRATIONS)
    assert stuck_report.total_score == 1.0
    assert stuck_report.final_snapshot["speech_loop"]["counters"]["stuck_states"] == 1


def test_speech_soak_suite_and_cli_json(capsys):
    suite = run_speech_soak_suite(fixtures_dir=FIXTURES, migrations_dir=MIGRATIONS)
    assert suite.to_dict()["total_score"] == 1.0

    exit_code = mneme_main([
        "eval",
        "speech",
        "--fixtures-dir",
        str(FIXTURES),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["suite"] is True
    assert payload["total_score"] == 1.0
    assert payload["passed_fixtures"] == payload["total_fixtures"]


def test_evaluation_logger_includes_speech_metrics(tmp_path):
    logger = EvaluationLogger(tmp_path / "eval.jsonl")
    logger.record_turn(
        input_text="hello",
        result={
            "timestamp": 1_000,
            "events": [],
            "utterances": [{"text": "hi", "plan": {"memory_refs": []}}],
            "snapshot": {
                "speech_loop": SpeechLoopDiagnostics().to_dict(),
            },
        },
    )

    summary = logger.summarize()

    assert "speech" in summary
    assert summary["speech"]["duplicate_suppressions_total"] == 0
