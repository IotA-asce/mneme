from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


LEVELS = {
    "L0": "reflex circuit",
    "L1": "simple nervous system",
    "L2": "insect-like benchmark evidence",
    "L3": "fish/reptile-like benchmark evidence",
    "L4": "mouse-like benchmark evidence",
    "L5": "dog/corvid-like benchmark evidence",
    "L6": "primate-like benchmark evidence",
    "L7": "human-assistant-like benchmark evidence",
    "L8": "human-brain-equivalent target",
}


@dataclass(slots=True)
class CapabilityLevelEvidence:
    level: str
    label: str
    passed: bool
    evidence: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "label": self.label,
            "passed": self.passed,
            "evidence": list(self.evidence),
            "missing": list(self.missing),
        }


@dataclass(slots=True)
class CapabilityReport:
    current_level: str
    current_label: str
    summary: str
    levels: list[CapabilityLevelEvidence] = field(default_factory=list)
    benchmark_reports: int = 0
    not_proven_yet: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_level": self.current_level,
            "current_label": self.current_label,
            "summary": self.summary,
            "benchmark_reports": self.benchmark_reports,
            "levels": [level.to_dict() for level in self.levels],
            "not_proven_yet": list(self.not_proven_yet),
            "animal_equivalence_claim": False,
        }


def current_runtime_capability_evidence() -> CapabilityReport:
    return CapabilityReport(
        current_level="L1",
        current_label=LEVELS["L1"],
        summary="Runtime components are present, but benchmark evidence has not been computed in this process.",
        benchmark_reports=0,
        levels=[
            CapabilityLevelEvidence("L0", LEVELS["L0"], True, evidence=["deterministic event-response loop exists"]),
            CapabilityLevelEvidence("L1", LEVELS["L1"], True, evidence=["working memory and safety-aware intent loop exist"]),
            CapabilityLevelEvidence("L2", LEVELS["L2"], False, missing=["run cognitive benchmarks"]),
        ],
        not_proven_yet=["L2", "L3", "L4", "L5", "L6", "L7", "L8"],
    )


def build_capability_report(reports: Sequence[Mapping[str, Any]]) -> CapabilityReport:
    report_list = [dict(report) for report in reports]
    if not report_list:
        return current_runtime_capability_evidence()

    category_scores: dict[str, float] = {}
    for report in report_list:
        for name, item in dict(report.get("category_scores", {})).items():
            if isinstance(item, Mapping):
                category_scores[name] = max(category_scores.get(name, 0.0), float(item.get("score", 0.0)))
            elif isinstance(item, (int, float)):
                category_scores[name] = max(category_scores.get(name, 0.0), float(item))

    levels = [
        CapabilityLevelEvidence("L0", LEVELS["L0"], True, evidence=["benchmark runner produced a report"]),
        CapabilityLevelEvidence(
            "L1",
            LEVELS["L1"],
            _passes(category_scores, "stuck_state_detection"),
            evidence=["responded without a stuck-state failure"] if _passes(category_scores, "stuck_state_detection") else [],
            missing=[] if _passes(category_scores, "stuck_state_detection") else ["stuck-state benchmark evidence"],
        ),
        CapabilityLevelEvidence(
            "L2",
            LEVELS["L2"],
            all(
                _passes(category_scores, name)
                for name in ("preference_recall", "hallucinated_memory", "provenance_correctness")
            ),
            evidence=[
                "preference recall passed",
                "hallucinated memory guard passed",
                "memory provenance refs were valid",
            ]
            if all(
                _passes(category_scores, name)
                for name in ("preference_recall", "hallucinated_memory", "provenance_correctness")
            )
            else [],
            missing=[
                label
                for name, label in (
                    ("preference_recall", "preference recall"),
                    ("hallucinated_memory", "hallucinated memory guard"),
                    ("provenance_correctness", "provenance correctness"),
                )
                if not _passes(category_scores, name)
            ],
        ),
        CapabilityLevelEvidence("L3", LEVELS["L3"], False, missing=["novelty/threat handling benchmarks"]),
        CapabilityLevelEvidence("L4", LEVELS["L4"], False, missing=["correction acceptance and person continuity benchmarks"]),
        CapabilityLevelEvidence("L5", LEVELS["L5"], False, missing=["social continuity and interruption soak benchmarks"]),
        CapabilityLevelEvidence("L6", LEVELS["L6"], False, missing=["multi-step planning benchmarks"]),
        CapabilityLevelEvidence("L7", LEVELS["L7"], False, missing=["reliable autobiographical abstraction benchmarks"]),
        CapabilityLevelEvidence("L8", LEVELS["L8"], False, missing=["long-term human-brain-equivalent target evidence"]),
    ]
    passed = [level for level in levels if level.passed]
    current = passed[-1] if passed else levels[0]
    not_proven = [level.level for level in levels if not level.passed]
    return CapabilityReport(
        current_level=current.level,
        current_label=current.label,
        summary=f"Current evidence supports {current.level} only. This is behavioral benchmark evidence, not animal equivalence.",
        levels=levels,
        benchmark_reports=len(report_list),
        not_proven_yet=not_proven,
    )


def _passes(category_scores: Mapping[str, float], name: str) -> bool:
    return category_scores.get(name, 0.0) >= 1.0
