from __future__ import annotations

import json
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .engine import DEFAULT_MIGRATIONS, ROOT, to_jsonable
from .live_perception import SpeechRecognitionBackend, SpeechTranscriptObservation
from .peripherals import PeripheralDevice
from .presence import SpeechOutput, SpeechOutputBackend
from .runtime_loop import MnemeRuntime, RuntimeClock


DEFAULT_SPEECH_FIXTURES_DIR = ROOT / "tests" / "fixtures" / "speech"


@dataclass(slots=True)
class SpeechSoakStep:
    advance_ms: int = 1_000
    expect: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.advance_ms = _positive_int(self.advance_ms, "advance_ms")
        self.expect = _json_mapping(self.expect, "expect")

    def to_dict(self) -> dict[str, Any]:
        return {
            "advance_ms": self.advance_ms,
            "expect": dict(self.expect),
        }


@dataclass(slots=True)
class SpeechSoakFixture:
    name: str
    steps: list[SpeechSoakStep]
    speech_inputs: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""
    virtual_speech_duration_ms: int = 0
    tts: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = _required_text(self.name, "name")
        if not self.steps:
            raise ValueError("speech soak fixture requires at least one step")
        self.speech_inputs = _mapping_list(self.speech_inputs, "speech_inputs")
        self.description = str(self.description)
        self.virtual_speech_duration_ms = _non_negative_int(
            self.virtual_speech_duration_ms,
            "virtual_speech_duration_ms",
        )
        self.tts = _json_mapping(self.tts, "tts")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "speech_inputs": [dict(item) for item in self.speech_inputs],
            "virtual_speech_duration_ms": self.virtual_speech_duration_ms,
            "tts": dict(self.tts),
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True)
class SpeechSoakStepResult:
    index: int
    passed: bool
    failures: list[str]
    speech_status: str | None
    utterance_count: int
    counters: dict[str, int]
    current_state: str
    processing_latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "passed": self.passed,
            "failures": list(self.failures),
            "speech_status": self.speech_status,
            "utterance_count": self.utterance_count,
            "counters": dict(self.counters),
            "current_state": self.current_state,
            "processing_latency_ms": self.processing_latency_ms,
        }


@dataclass(slots=True)
class SpeechSoakReport:
    fixture_name: str
    total_score: float
    passed_steps: int
    total_steps: int
    failed_expectations: list[str]
    final_snapshot: dict[str, Any]
    steps: list[SpeechSoakStepResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_name": self.fixture_name,
            "total_score": self.total_score,
            "passed_steps": self.passed_steps,
            "total_steps": self.total_steps,
            "failed_expectations": list(self.failed_expectations),
            "final_snapshot": to_jsonable(self.final_snapshot),
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True)
class SpeechSoakSuiteReport:
    fixture_reports: list[SpeechSoakReport]

    def to_dict(self) -> dict[str, Any]:
        reports = [report.to_dict() for report in self.fixture_reports]
        total = len(reports)
        passed = sum(1 for report in self.fixture_reports if report.total_score >= 1.0)
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
        }


class FixtureSpeechRecognitionBackend(SpeechRecognitionBackend):
    def __init__(self, inputs: Sequence[Mapping[str, Any]]) -> None:
        self.inputs = [dict(item) for item in inputs]
        self.index = 0

    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        if self.index >= len(self.inputs):
            return None
        item = self.inputs[self.index]
        self.index += 1
        status = str(item.get("status", "transcript"))
        if status == "no_speech":
            return None
        if status == "error":
            raise ValueError(str(item.get("error", "fixture_asr_error")))
        text = _required_text(item.get("transcript", item.get("text")), "transcript")
        return SpeechTranscriptObservation(
            transcript_id=str(item.get("transcript_id", f"fixture_transcript_{self.index}")),
            captured_ts=timestamp,
            device_id=device.device_id,
            device_label=device.label,
            speaker=str(item.get("speaker", "user")),
            transcript=text,
            confidence=float(item.get("confidence", 0.9)),
            duration_ms=item.get("duration_ms"),
            metadata={"backend": "speech_soak_fixture", **dict(item.get("metadata", {}))},
        )


class FixtureSpeechOutputBackend(SpeechOutputBackend):
    def __init__(self, *, fail_on_calls: Sequence[int] | None = None) -> None:
        self.fail_on_calls = set(int(item) for item in (fail_on_calls or []))
        self.calls = 0
        self.outputs: list[SpeechOutput] = []

    def speak(
        self,
        *,
        text: str,
        voice: str | None,
        device_id: str | None,
        timestamp: int,
    ) -> SpeechOutput:
        self.calls += 1
        if self.calls in self.fail_on_calls:
            raise ValueError("fixture_tts_failure")
        output = SpeechOutput(
            output_id=f"fixture_speech_{self.calls}",
            text=text,
            created_ts=timestamp,
            status="spoken",
            voice=voice,
            device_id=device_id,
            metadata={"backend": "speech_soak_fixture", "call": self.calls},
        )
        self.outputs.append(output)
        return output


def load_speech_soak_fixture(path: str | Path) -> SpeechSoakFixture:
    fixture_path = Path(path)
    raw = fixture_path.read_text(encoding="utf-8")
    data = json.loads(raw) if fixture_path.suffix.lower() == ".json" else yaml.safe_load(raw)
    if not isinstance(data, Mapping):
        raise ValueError("speech soak fixture must be a mapping")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("speech soak fixture requires at least one step")
    return SpeechSoakFixture(
        name=_required_text(data.get("name"), "name"),
        description=str(data.get("description", "")),
        speech_inputs=_mapping_list(data.get("speech_inputs", []), "speech_inputs"),
        virtual_speech_duration_ms=int(data.get("virtual_speech_duration_ms", 0)),
        tts=dict(data.get("tts", {})),
        steps=[
            SpeechSoakStep(
                advance_ms=int(step.get("advance_ms", 1_000)),
                expect=dict(step.get("expect", {})),
            )
            for step in steps
            if isinstance(step, Mapping)
        ],
    )


def run_speech_soak(
    fixture: str | Path | SpeechSoakFixture,
    *,
    db_path: str | Path | None = None,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS,
) -> SpeechSoakReport:
    loaded = load_speech_soak_fixture(fixture) if not isinstance(fixture, SpeechSoakFixture) else fixture
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="mneme-speech-soak-") as tmp_dir:
            return _run_with_db(loaded, Path(tmp_dir) / "memory.sqlite3", migrations_dir)
    return _run_with_db(loaded, Path(db_path), migrations_dir)


def run_speech_soak_suite(
    fixtures: Sequence[str | Path] | None = None,
    *,
    fixtures_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS,
) -> SpeechSoakSuiteReport:
    fixture_paths = list(fixtures or [])
    if fixtures_dir is not None:
        fixture_paths.extend(_fixture_paths(Path(fixtures_dir)))
    if not fixture_paths:
        fixture_paths = _fixture_paths(DEFAULT_SPEECH_FIXTURES_DIR)
    return SpeechSoakSuiteReport([
        run_speech_soak(path, db_path=db_path, migrations_dir=migrations_dir)
        for path in fixture_paths
    ])


def _run_with_db(
    fixture: SpeechSoakFixture,
    db_path: Path,
    migrations_dir: str | Path,
) -> SpeechSoakReport:
    runtime = MnemeRuntime(
        db_path=db_path,
        migrations_dir=migrations_dir,
        clock=RuntimeClock(1_000),
        live_speech_backend=FixtureSpeechRecognitionBackend(fixture.speech_inputs),
        speech_output_backend=FixtureSpeechOutputBackend(
            fail_on_calls=fixture.tts.get("fail_on_calls", []),
        ),
        virtual_speech_duration_ms=fixture.virtual_speech_duration_ms,
    )
    try:
        runtime.start()
        step_results: list[SpeechSoakStepResult] = []
        for index, step in enumerate(fixture.steps, start=1):
            started = time.perf_counter()
            result = runtime.tick(advance_ms=step.advance_ms)
            latency_ms = int((time.perf_counter() - started) * 1000)
            step_results.append(_score_step(index, step, result.to_dict(), latency_ms))
        final_snapshot = runtime.snapshot()
        failures = [
            failure
            for step_result in step_results
            for failure in step_result.failures
        ]
        passed = sum(1 for step_result in step_results if step_result.passed)
        total = len(step_results)
        return SpeechSoakReport(
            fixture_name=fixture.name,
            total_score=round(passed / total, 6) if total else 0.0,
            passed_steps=passed,
            total_steps=total,
            failed_expectations=failures,
            final_snapshot=final_snapshot,
            steps=step_results,
        )
    finally:
        runtime.close()


def _score_step(
    index: int,
    step: SpeechSoakStep,
    result: Mapping[str, Any],
    processing_latency_ms: int,
) -> SpeechSoakStepResult:
    snapshot = result.get("snapshot", {})
    speech_loop = snapshot.get("speech_loop", {}) if isinstance(snapshot, Mapping) else {}
    counters = (
        dict(speech_loop.get("counters", {}))
        if isinstance(speech_loop, Mapping) and isinstance(speech_loop.get("counters"), Mapping)
        else {}
    )
    latest_report = (
        speech_loop.get("latest_capture_report", {})
        if isinstance(speech_loop, Mapping)
        else {}
    )
    latest_report = latest_report if isinstance(latest_report, Mapping) else {}
    utterances = result.get("utterances", [])
    utterance_count = len(utterances) if isinstance(utterances, list) else 0
    current_state = (
        str(speech_loop.get("current_state", "unknown"))
        if isinstance(speech_loop, Mapping)
        else "unknown"
    )
    failures = _expect_failures(
        index,
        step.expect,
        speech_status=latest_report.get("status"),
        utterance_count=utterance_count,
        counters=counters,
        current_state=current_state,
        speech_loop=speech_loop if isinstance(speech_loop, Mapping) else {},
    )
    return SpeechSoakStepResult(
        index=index,
        passed=not failures,
        failures=failures,
        speech_status=str(latest_report.get("status")) if latest_report else None,
        utterance_count=utterance_count,
        counters={key: int(value) for key, value in counters.items() if isinstance(value, int)},
        current_state=current_state,
        processing_latency_ms=processing_latency_ms,
    )


def _expect_failures(
    index: int,
    expect: Mapping[str, Any],
    *,
    speech_status: Any,
    utterance_count: int,
    counters: Mapping[str, Any],
    current_state: str,
    speech_loop: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    if "speech_status" in expect and speech_status != expect["speech_status"]:
        failures.append(
            f"step {index}: expected speech_status={expect['speech_status']}, got {speech_status}"
        )
    if "current_state" in expect and current_state != expect["current_state"]:
        failures.append(
            f"step {index}: expected current_state={expect['current_state']}, got {current_state}"
        )
    if "utterance_count" in expect and utterance_count != int(expect["utterance_count"]):
        failures.append(
            f"step {index}: expected utterance_count={expect['utterance_count']}, got {utterance_count}"
        )
    if "latest_failure_contains" in expect:
        reason = str(speech_loop.get("latest_failure_reason", ""))
        if str(expect["latest_failure_contains"]) not in reason:
            failures.append(
                f"step {index}: latest failure did not contain {expect['latest_failure_contains']}"
            )
    for key, expected in expect.items():
        if not key.endswith("_total"):
            continue
        counter_name = key.removesuffix("_total")
        actual = int(counters.get(counter_name, 0))
        if actual != int(expected):
            failures.append(f"step {index}: expected {key}={expected}, got {actual}")
    return failures


def _fixture_paths(fixtures_dir: Path) -> list[Path]:
    if not fixtures_dir.exists():
        return []
    return sorted([
        path
        for path in fixtures_dir.iterdir()
        if path.suffix.lower() in {".yaml", ".yml", ".json"}
    ])


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    items = list(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError(f"{field_name} must contain mappings")
    return [dict(item) for item in items]


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value
