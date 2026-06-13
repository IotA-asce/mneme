import json
from pathlib import Path

from android_brain_memory import load_benchmark_fixture, run_cognitive_benchmark
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "cognition" / "basic_preference_recall.yaml"


def test_load_benchmark_fixture_parses_yaml():
    fixture = load_benchmark_fixture(FIXTURE)

    assert fixture.name == "basic_preference_recall"
    assert len(fixture.steps) == 3
    assert fixture.steps[1].expect["memory_ref_required"] is True


def test_cognitive_benchmark_replays_runtime_and_scores(tmp_path):
    report = run_cognitive_benchmark(
        FIXTURE,
        db_path=tmp_path / "benchmark.sqlite3",
        migrations_dir=MIGRATIONS,
    )
    payload = report.to_dict()

    assert payload["total_score"] == 1.0
    assert payload["memory_refs_used"]
    assert payload["category_scores"]["preference_recall"]["score"] == 1.0
    assert payload["category_scores"]["hallucinated_memory"]["score"] == 1.0
    assert payload["category_scores"]["provenance_correctness"]["score"] == 1.0
    assert payload["capability_ladder"]["current_level"] == "L2"


def test_cognitive_benchmark_reports_failed_expectations(tmp_path):
    fixture = tmp_path / "bad.yaml"
    fixture.write_text(
        """
name: bad_expectation
category: preference_recall
steps:
  - input: "hello Mneme"
    expect:
      response_contains: ["not present"]
""",
        encoding="utf-8",
    )

    report = run_cognitive_benchmark(
        fixture,
        db_path=tmp_path / "bad.sqlite3",
        migrations_dir=MIGRATIONS,
    )

    assert report.total_score == 0.0
    assert report.failed_expectations


def test_mneme_eval_cognition_json_cli(tmp_path, capsys):
    exit_code = mneme_main([
        "--migrations",
        str(MIGRATIONS),
        "eval",
        "cognition",
        "--fixture",
        str(FIXTURE),
        "--benchmark-db",
        str(tmp_path / "cli-benchmark.sqlite3"),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["fixture_name"] == "basic_preference_recall"
    assert payload["total_score"] == 1.0
