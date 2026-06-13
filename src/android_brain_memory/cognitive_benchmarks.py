from __future__ import annotations

import json
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .capability_ladder import build_capability_report
from .engine import DEFAULT_MIGRATIONS, ROOT, to_jsonable
from .runtime_loop import MnemeRuntime, RuntimeClock


DEFAULT_COGNITION_FIXTURE = ROOT / "tests" / "fixtures" / "cognition" / "basic_preference_recall.yaml"
DEFAULT_COGNITION_FIXTURES_DIR = ROOT / "tests" / "fixtures" / "cognition"
MEMORY_CLAIM_PHRASES = ("you told me", "you said", "i remember", "i observed")


@dataclass(slots=True)
class BenchmarkStep:
    input: str
    timestamp: int | None = None
    expect: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "timestamp": self.timestamp,
            "expect": dict(self.expect),
        }


@dataclass(slots=True)
class BenchmarkFixture:
    name: str
    category: str
    steps: list[BenchmarkStep]
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True)
class BenchmarkStepResult:
    index: int
    input: str
    passed: bool
    failures: list[str]
    response_text: str
    memory_refs: list[dict[str, str]]
    turn_type: str | None
    act_type: str | None
    model_realized: bool
    deterministic_fallback: bool
    latency_ms: int
    category_scores: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "input": self.input,
            "passed": self.passed,
            "failures": list(self.failures),
            "response_text": self.response_text,
            "memory_refs": [dict(ref) for ref in self.memory_refs],
            "turn_type": self.turn_type,
            "act_type": self.act_type,
            "model_realized": self.model_realized,
            "deterministic_fallback": self.deterministic_fallback,
            "latency_ms": self.latency_ms,
            "category_scores": dict(self.category_scores),
        }


@dataclass(slots=True)
class CognitiveBenchmarkReport:
    fixture_name: str
    category: str
    total_score: float
    passed_steps: int
    total_steps: int
    failed_expectations: list[str]
    memory_refs_used: list[dict[str, str]]
    model_realized_turns: int
    deterministic_fallback_turns: int
    category_scores: dict[str, dict[str, Any]]
    capability_ladder: dict[str, Any]
    steps: list[BenchmarkStepResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_name": self.fixture_name,
            "category": self.category,
            "total_score": self.total_score,
            "passed_steps": self.passed_steps,
            "total_steps": self.total_steps,
            "failed_expectations": list(self.failed_expectations),
            "memory_refs_used": [dict(ref) for ref in self.memory_refs_used],
            "model_realized_turns": self.model_realized_turns,
            "deterministic_fallback_turns": self.deterministic_fallback_turns,
            "category_scores": to_jsonable(self.category_scores),
            "capability_ladder": dict(self.capability_ladder),
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True)
class CognitiveBenchmarkSuiteReport:
    fixture_reports: list[CognitiveBenchmarkReport]

    def to_dict(self) -> dict[str, Any]:
        reports = [report.to_dict() for report in self.fixture_reports]
        passed = sum(1 for report in self.fixture_reports if report.total_score >= 1.0)
        total = len(self.fixture_reports)
        score = (
            round(sum(report.total_score for report in self.fixture_reports) / total, 6)
            if total
            else 0.0
        )
        return {
            "suite": True,
            "total_score": score,
            "passed_fixtures": passed,
            "total_fixtures": total,
            "failed_expectations": [
                failure
                for report in self.fixture_reports
                for failure in report.failed_expectations
            ],
            "fixture_reports": reports,
            "capability_ladder": build_capability_report(reports).to_dict(),
        }


def load_benchmark_fixture(path: str | Path) -> BenchmarkFixture:
    fixture_path = Path(path)
    raw = fixture_path.read_text(encoding="utf-8")
    data = json.loads(raw) if fixture_path.suffix.lower() == ".json" else yaml.safe_load(raw)
    if not isinstance(data, Mapping):
        raise ValueError("benchmark fixture must be a mapping")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("benchmark fixture requires at least one step")
    return BenchmarkFixture(
        name=_text(data.get("name"), "name"),
        description=str(data.get("description", "")),
        category=str(data.get("category", "general")),
        steps=[
            BenchmarkStep(
                input=_text(step.get("input"), "step.input"),
                timestamp=step.get("timestamp"),
                expect=dict(step.get("expect", {})),
            )
            for step in steps
            if isinstance(step, Mapping)
        ],
    )


def run_cognitive_benchmark(
    fixture: str | Path | BenchmarkFixture,
    *,
    db_path: str | Path | None = None,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS,
) -> CognitiveBenchmarkReport:
    loaded = load_benchmark_fixture(fixture) if not isinstance(fixture, BenchmarkFixture) else fixture
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="mneme-cognition-benchmark-") as tmp_dir:
            return _run_with_db(loaded, Path(tmp_dir) / "memory.sqlite3", migrations_dir)
    return _run_with_db(loaded, Path(db_path), migrations_dir)


def run_cognitive_benchmark_suite(
    fixtures: Sequence[str | Path] | None = None,
    *,
    fixtures_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS,
) -> CognitiveBenchmarkSuiteReport:
    fixture_paths = list(fixtures or [])
    if fixtures_dir is not None:
        fixture_paths.extend(_fixture_paths(Path(fixtures_dir)))
    if not fixture_paths:
        fixture_paths = _fixture_paths(DEFAULT_COGNITION_FIXTURES_DIR)
    reports = [
        run_cognitive_benchmark(path, db_path=db_path, migrations_dir=migrations_dir)
        for path in fixture_paths
    ]
    return CognitiveBenchmarkSuiteReport(reports)


def _run_with_db(
    fixture: BenchmarkFixture,
    db_path: Path,
    migrations_dir: str | Path,
) -> CognitiveBenchmarkReport:
    runtime = MnemeRuntime(
        db_path=db_path,
        migrations_dir=migrations_dir,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        step_results: list[BenchmarkStepResult] = []
        now = 1_000
        for index, step in enumerate(fixture.steps, start=1):
            now = step.timestamp if step.timestamp is not None else now + 1_000
            started = time.perf_counter()
            result = runtime.process_user_utterance(step.input, timestamp=now)
            latency_ms = int((time.perf_counter() - started) * 1000)
            step_results.append(_score_step(index, step, result.to_dict(), latency_ms, runtime))
        return _report(fixture, step_results)
    finally:
        runtime.close()


def _score_step(
    index: int,
    step: BenchmarkStep,
    result: Mapping[str, Any],
    latency_ms: int,
    runtime: MnemeRuntime,
) -> BenchmarkStepResult:
    utterances = result.get("utterances", [])
    latest = utterances[-1] if isinstance(utterances, list) and utterances else {}
    plan = latest.get("plan", {}) if isinstance(latest, Mapping) else {}
    text = str(latest.get("text", "")) if isinstance(latest, Mapping) else ""
    refs = _memory_refs(plan.get("memory_refs", []) if isinstance(plan, Mapping) else [])
    slots = plan.get("content_slots", {}) if isinstance(plan, Mapping) else {}
    realization = slots.get("model_realization", {}) if isinstance(slots, Mapping) else {}
    snapshot = result.get("snapshot", {}) if isinstance(result.get("snapshot"), Mapping) else {}
    turn_type = _latest_turn_type(snapshot)
    expect = step.expect
    review_action_result: dict[str, Any] | None = None
    if expect.get("apply_latest_review"):
        latest_review = _latest_review(snapshot)
        review_id = latest_review.get("review_id")
        if isinstance(review_id, str) and review_id:
            record = runtime.apply_review(
                review_id,
                reason="benchmark expectation",
            )
            review_action_result = record.get("action_result") if isinstance(record, Mapping) else None
            snapshot = runtime.snapshot()
        else:
            review_action_result = {
                "error": "no latest review proposal to apply",
            }
    failures: list[str] = []
    category_scores = {
        "hallucinated_memory": True,
        "provenance_correctness": True,
        "stuck_state_detection": True,
        "response_latency": True,
        "model_fallback_rate": True,
    }
    for name in expect.get("category_tags", []):
        category_scores[str(name)] = True
    if expect.get("memory_ref_required"):
        category_scores.setdefault("preference_recall", True)
    if expect.get("contradiction_clarification"):
        category_scores.setdefault("contradiction_handling", True)
    if expect.get("correction_proposal"):
        category_scores.setdefault("correction_acceptance", True)
    if expect.get("review_proposal_required"):
        category_scores.setdefault("review_proposal", True)

    for phrase in expect.get("response_contains", []):
        if str(phrase).lower() not in text.lower():
            failures.append(f"response did not contain: {phrase}")
    for phrase in expect.get("response_not_contains", []):
        if str(phrase).lower() in text.lower():
            failures.append(f"response unexpectedly contained: {phrase}")
    if expect.get("memory_ref_required") and not refs:
        failures.append("response did not include a memory reference")
        category_scores["preference_recall"] = False
    if expect.get("memory_ref_forbidden") and refs:
        failures.append("response unexpectedly included a memory reference")
        category_scores["hallucinated_memory"] = False
    expected_turn = expect.get("turn_type")
    if expected_turn and turn_type != expected_turn:
        failures.append(f"turn_type was {turn_type}, expected {expected_turn}")
    expected_act = expect.get("act_type")
    if expected_act and plan.get("act_type") != expected_act:
        failures.append(f"act_type was {plan.get('act_type')}, expected {expected_act}")
    if expect.get("correction_proposal"):
        proposal = snapshot.get("memory_review", {}).get("last_correction_proposal") if isinstance(snapshot.get("memory_review"), Mapping) else None
        if not proposal:
            failures.append("expected a correction proposal")
            category_scores["correction_acceptance"] = False
    if expect.get("review_proposal_required"):
        proposal = _latest_review(snapshot)
        if not proposal:
            failures.append("expected a memory review proposal")
            category_scores["correction_acceptance"] = False
            category_scores["review_proposal"] = False
    expected_review_type = expect.get("review_type")
    if expected_review_type:
        proposal = _latest_review(snapshot)
        if proposal.get("proposal_type") != expected_review_type:
            failures.append(f"review_type was {proposal.get('proposal_type')}, expected {expected_review_type}")
            category_scores["correction_acceptance"] = False
            category_scores["review_proposal"] = False
    expected_review_status = expect.get("review_status")
    if expected_review_status:
        proposal = _latest_review(snapshot)
        if proposal.get("status") != expected_review_status:
            failures.append(f"review_status was {proposal.get('status')}, expected {expected_review_status}")
            category_scores["correction_acceptance"] = False
            category_scores["review_proposal"] = False
    expected_counts = expect.get("fact_status_counts")
    if isinstance(expected_counts, Mapping):
        counts = runtime.engine.inspect_db().get("facts_by_status", {})
        for status, expected_count in expected_counts.items():
            if counts.get(status, 0) != expected_count:
                failures.append(f"fact status {status} count was {counts.get(status, 0)}, expected {expected_count}")
    if expect.get("conflict_report_required") and not runtime.engine.store.get_fact_conflict_reports():
        failures.append("expected at least one fact conflict report")
        category_scores["contradiction_handling"] = False
    expected_source = expect.get("fact_source_type")
    if expected_source:
        if not _has_fact_source(runtime, expected_source, refs, review_action_result):
            failures.append(f"expected fact source_type {expected_source}")
            category_scores["provenance_correctness"] = False
    if expect.get("model_realized") is not None:
        used = bool(realization.get("used_model")) if isinstance(realization, Mapping) else False
        if used != bool(expect["model_realized"]):
            failures.append(f"model realization was {used}, expected {expect['model_realized']}")
    max_latency = expect.get("max_latency_ms")
    if isinstance(max_latency, int) and latency_ms > max_latency:
        failures.append(f"latency {latency_ms} ms exceeded {max_latency} ms")
        category_scores["response_latency"] = False
    if not text:
        failures.append("no response generated")
        category_scores["stuck_state_detection"] = False
    if _has_unsupported_memory_claim(text, refs, expect):
        failures.append("response made a memory claim without memory refs")
        category_scores["hallucinated_memory"] = False
    if not _refs_exist(runtime, refs):
        failures.append("one or more memory refs do not resolve")
        category_scores["provenance_correctness"] = False
    if expect.get("contradiction_clarification") and "conflict" not in text.lower() and "clarif" not in text.lower():
        failures.append("expected contradiction clarification language")
        category_scores["contradiction_handling"] = False

    return BenchmarkStepResult(
        index=index,
        input=step.input,
        passed=not failures,
        failures=failures,
        response_text=text,
        memory_refs=refs,
        turn_type=turn_type,
        act_type=str(plan.get("act_type")) if isinstance(plan, Mapping) and plan.get("act_type") else None,
        model_realized=bool(realization.get("used_model")) if isinstance(realization, Mapping) else False,
        deterministic_fallback=not bool(realization.get("used_model")) if isinstance(realization, Mapping) else True,
        latency_ms=latency_ms,
        category_scores=category_scores,
    )


def _report(fixture: BenchmarkFixture, steps: list[BenchmarkStepResult]) -> CognitiveBenchmarkReport:
    passed = sum(1 for step in steps if step.passed)
    failed = [
        f"step {step.index}: {failure}"
        for step in steps
        for failure in step.failures
    ]
    category_scores: dict[str, dict[str, Any]] = {}
    category_names = sorted({name for step in steps for name in step.category_scores})
    for name in category_names:
        applicable = [step.category_scores[name] for step in steps if name in step.category_scores]
        passed_count = sum(1 for item in applicable if item)
        category_scores[name] = {
            "passed": passed_count,
            "total": len(applicable),
            "score": round(passed_count / len(applicable), 6) if applicable else 0.0,
        }
    refs = []
    for step in steps:
        refs.extend(step.memory_refs)
    report = CognitiveBenchmarkReport(
        fixture_name=fixture.name,
        category=fixture.category,
        total_score=round(passed / len(steps), 6) if steps else 0.0,
        passed_steps=passed,
        total_steps=len(steps),
        failed_expectations=failed,
        memory_refs_used=refs,
        model_realized_turns=sum(1 for step in steps if step.model_realized),
        deterministic_fallback_turns=sum(1 for step in steps if step.deterministic_fallback),
        category_scores=category_scores,
        capability_ladder={},
        steps=steps,
    )
    report.capability_ladder = build_capability_report([report.to_dict()]).to_dict()
    return report


def _latest_turn_type(snapshot: Mapping[str, Any]) -> str | None:
    working = snapshot.get("working_memory")
    if not isinstance(working, Mapping):
        return None
    turns = working.get("recent_dialogue_turns")
    if not isinstance(turns, list) or not turns:
        return None
    latest = turns[-1]
    if not isinstance(latest, Mapping):
        return None
    classification = latest.get("turn_classification")
    if isinstance(classification, Mapping):
        turn_type = classification.get("turn_type")
        return str(turn_type) if turn_type else None
    return None


def _latest_review(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    review = snapshot.get("memory_review")
    if not isinstance(review, Mapping):
        return {}
    latest = review.get("last_correction_proposal")
    return latest if isinstance(latest, Mapping) else {}


def _has_fact_source(
    runtime: MnemeRuntime,
    expected_source: str,
    refs: list[dict[str, str]],
    review_action_result: Mapping[str, Any] | None,
) -> bool:
    fact_ids = [
        ref["memory_id"]
        for ref in refs
        if ref["memory_kind"] == "fact"
    ]
    if isinstance(review_action_result, Mapping):
        created = review_action_result.get("created_fact_ids")
        if isinstance(created, list):
            fact_ids.extend(item for item in created if isinstance(item, str))
        changed = review_action_result.get("changed_memory_refs")
        if isinstance(changed, list):
            fact_ids.extend(
                item["memory_id"]
                for item in changed
                if isinstance(item, Mapping)
                and item.get("memory_kind") == "fact"
                and isinstance(item.get("memory_id"), str)
            )
    for fact_id in dict.fromkeys(fact_ids):
        fact = runtime.engine.store.get_fact(fact_id)
        if fact is not None and fact.source_type.value == expected_source:
            return True
    return False


def _has_unsupported_memory_claim(text: str, refs: list[dict[str, str]], expect: Mapping[str, Any]) -> bool:
    if refs or expect.get("allow_memory_claim_without_ref"):
        return False
    lower = text.lower()
    return any(phrase in lower for phrase in MEMORY_CLAIM_PHRASES)


def _refs_exist(runtime: MnemeRuntime, refs: list[dict[str, str]]) -> bool:
    for ref in refs:
        kind = ref["memory_kind"]
        memory_id = ref["memory_id"]
        if kind == "fact" and runtime.engine.store.get_fact(memory_id) is None:
            return False
        if kind == "episode" and runtime.engine.store.get_episode(memory_id) is None:
            return False
    return True


def _memory_refs(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    refs = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        kind = item.get("memory_kind")
        memory_id = item.get("memory_id")
        if isinstance(kind, str) and isinstance(memory_id, str):
            refs.append({"memory_kind": kind, "memory_id": memory_id})
    return refs


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _fixture_paths(fixtures_dir: Path) -> list[Path]:
    if not fixtures_dir.exists():
        return []
    return sorted(
        path
        for path in fixtures_dir.iterdir()
        if path.suffix.lower() in {".yaml", ".yml", ".json"}
    )
