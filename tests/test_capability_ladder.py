import json
from pathlib import Path

from android_brain_memory import build_capability_report, current_runtime_capability_evidence, run_cognitive_benchmark
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "cognition" / "basic_preference_recall.yaml"


def test_capability_report_is_conservative_without_benchmarks():
    report = current_runtime_capability_evidence().to_dict()

    assert report["current_level"] == "L1"
    assert report["animal_equivalence_claim"] is False
    assert "L2" in report["not_proven_yet"]


def test_capability_report_uses_benchmark_evidence(tmp_path):
    benchmark = run_cognitive_benchmark(
        FIXTURE,
        db_path=tmp_path / "capability.sqlite3",
        migrations_dir=MIGRATIONS,
    )
    report = build_capability_report([benchmark.to_dict()]).to_dict()

    assert report["current_level"] == "L2"
    assert report["animal_equivalence_claim"] is False
    assert "L3" in report["not_proven_yet"]


def test_mneme_eval_capability_json_cli(tmp_path, capsys):
    exit_code = mneme_main([
        "--migrations",
        str(MIGRATIONS),
        "eval",
        "capability",
        "--fixture",
        str(FIXTURE),
        "--benchmark-db",
        str(tmp_path / "capability-cli.sqlite3"),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_level"] == "L2"
    assert payload["animal_equivalence_claim"] is False


def test_mneme_eval_capability_default_suite_reaches_l3(capsys):
    exit_code = mneme_main([
        "--migrations",
        str(MIGRATIONS),
        "eval",
        "capability",
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_level"] == "L3"
    assert payload["animal_equivalence_claim"] is False
