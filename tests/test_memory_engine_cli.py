from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from android_brain_memory import ConsolidationOptions, Episode, Fact, MnemeMemory


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "storage" / "migrations"


def memory_candidate_payload(candidate_id: str = "cand_calibration_001") -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "dialogue_turn",
        "summary": "User asked Mneme to remember the calibration routine.",
        "source_type": "user_confirmed",
        "confidence": 0.95,
        "features": {
            "novelty": 0.8,
            "task_relevance": 0.9,
            "social_relevance": 0.4,
            "surprise": 0.3,
            "risk": 0.0,
            "contradiction": 0.0,
            "repetition_signal": 0.7,
            "explicit_remember_flag": 1.0,
        },
        "entities": ["user"],
        "tags": ["calibration"],
        "payload": {"topic": "calibration routine"},
    }


def calibration_episode_payload(episode_id: str, start_ts: int, summary: str) -> dict:
    return {
        "episode_id": episode_id,
        "start_ts": start_ts,
        "end_ts": start_ts + 10,
        "summary": summary,
        "context": {"topic": "calibration routine", "tags": ["calibration"]},
        "salience": 0.82,
        "confidence": 0.9,
        "participants": ["user"],
        "objects": [],
        "provenance_refs": [],
    }


def calibration_fact_payload(supporting_episode_id: str = "ep_calibration_001") -> dict:
    return {
        "fact_id": "fact_calibration_routine",
        "subject": "user",
        "predicate": "practices",
        "object_value": {"value": "calibration routine"},
        "confidence": 0.95,
        "source_type": "user_confirmed",
        "status": "active",
        "tags": ["calibration"],
        "supporting_episode_ids": [supporting_episode_id],
    }


def test_mneme_memory_facade_conversation_like_flow(tmp_path):
    with MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS) as memory:
        applied = memory.init_db()
        assert [record.migration_id for record in applied] == [
            "001_init",
            "002_fact_tags",
            "003_memory_review",
        ]

        remembered = memory.remember_candidate(
            memory_candidate_payload(),
            create_episode=True,
            episode_id="ep_calibration_001",
            start_ts=100,
            end_ts=110,
            participants=["user"],
            context={"topic": "calibration routine", "tags": ["calibration"]},
        )
        assert remembered.trace_id is not None
        assert remembered.episode is not None
        assert remembered.salience.decision == "episode_and_semantic_candidate"

        memory.add_episode(
            Episode.from_dict(
                calibration_episode_payload(
                    "ep_calibration_002",
                    160,
                    "User repeated the calibration routine at the bench.",
                )
            )
        )
        memory.add_episode(
            Episode.from_dict(
                calibration_episode_payload(
                    "ep_calibration_003",
                    220,
                    "User finished another calibration routine.",
                )
            )
        )
        fact_result = memory.add_fact(Fact.from_dict(calibration_fact_payload()))
        assert fact_result.conflict_report is None

        bundle = memory.retrieve({"query_text": "calibration", "max_results": 5})
        assert [fact.fact_id for fact in bundle.facts] == ["fact_calibration_routine"]
        assert {episode.episode_id for episode in bundle.episodes} >= {
            "ep_calibration_001",
            "ep_calibration_002",
            "ep_calibration_003",
        }
        assert bundle.ranking_explanations

        report = memory.consolidate_once(
            ConsolidationOptions(min_repetition=3, close_time_window_s=600)
        )
        assert report.summaries_created == 1
        assert report.summary_ids

        inspection = memory.inspect_db()
        assert inspection["table_counts"]["raw_trace"] == 1
        assert inspection["table_counts"]["episode"] == 3
        assert inspection["table_counts"]["fact"] == 1
        assert inspection["table_counts"]["memory_summary"] == 1


def test_memory_cli_conversation_like_flow_outputs_json(tmp_path):
    db_path = tmp_path / "memory.sqlite3"
    candidate_file = _write_json(
        tmp_path / "candidate.json",
        memory_candidate_payload("cand_cli_001"),
    )
    episode_two_file = _write_json(
        tmp_path / "episode_two.json",
        calibration_episode_payload(
            "ep_cli_calibration_002",
            160,
            "User repeated the calibration routine at the bench.",
        ),
    )
    episode_three_file = _write_json(
        tmp_path / "episode_three.json",
        calibration_episode_payload(
            "ep_cli_calibration_003",
            220,
            "User finished another calibration routine.",
        ),
    )
    fact_file = _write_json(
        tmp_path / "fact.json",
        calibration_fact_payload("ep_cli_calibration_001"),
    )

    initialized = _run_cli(db_path, "init-db")
    assert initialized["command"] == "init-db"
    assert [record["migration_id"] for record in initialized["applied_migrations"]] == [
        "001_init",
        "002_fact_tags",
        "003_memory_review",
    ]

    remembered = _run_cli(
        db_path,
        "remember-candidate",
        "--file",
        str(candidate_file),
        "--episode",
        "--episode-id",
        "ep_cli_calibration_001",
        "--start-ts",
        "100",
        "--end-ts",
        "110",
        "--participant",
        "user",
        "--context-json",
        '{"topic": "calibration routine", "tags": ["calibration"]}',
    )
    assert remembered["result"]["trace_id"].startswith("trace_")
    assert remembered["result"]["episode"]["episode_id"] == "ep_cli_calibration_001"
    assert remembered["result"]["salience"]["decision"] == "episode_and_semantic_candidate"

    _run_cli(db_path, "add-episode", "--file", str(episode_two_file))
    _run_cli(db_path, "add-episode", "--file", str(episode_three_file))

    fact_result = _run_cli(db_path, "add-fact", "--file", str(fact_file))
    assert fact_result["result"]["fact"]["fact_id"] == "fact_calibration_routine"
    assert fact_result["result"]["conflict_report"] is None

    retrieved = _run_cli(
        db_path,
        "retrieve",
        "--query-text",
        "calibration",
        "--max-results",
        "5",
    )
    assert retrieved["bundle"]["facts"][0]["fact_id"] == "fact_calibration_routine"
    assert retrieved["bundle"]["ranking_explanations"]

    consolidated = _run_cli(
        db_path,
        "consolidate-once",
        "--min-repetition",
        "3",
        "--close-time-window-s",
        "600",
    )
    assert consolidated["report"]["summaries_created"] == 1
    assert len(consolidated["report"]["summary_ids"]) == 1

    inspected = _run_cli(db_path, "inspect-db")
    assert inspected["inspection"]["table_counts"]["raw_trace"] == 1
    assert inspected["inspection"]["table_counts"]["episode"] == 3
    assert inspected["inspection"]["table_counts"]["fact"] == 1
    assert inspected["inspection"]["table_counts"]["memory_summary"] == 1


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run_cli(db_path: Path, *args: str) -> dict:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(ROOT / "src")
        if not existing_pythonpath
        else f"{ROOT / 'src'}{os.pathsep}{existing_pythonpath}"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "android_brain_memory.cli",
            "--db",
            str(db_path),
            "--migrations",
            str(MIGRATIONS),
            *args,
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)
