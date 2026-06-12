from __future__ import annotations

import re
from typing import Any

from .engine import MnemeMemory
from .models import Fact, MemoryStatus, SourceType, parse_source_type

SELF_SUBJECT = "self"
PROCEDURE_PREDICATE_PREFIX = "procedure:"
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slug(value: str) -> str:
    return _SLUG_PATTERN.sub("_", value.strip().lower()).strip("_")


class SelfModel:
    """Persistent identity facts about the robot itself (self model v0).

    Identity updates are deliberate replacements: each predicate has one
    fixed fact ID, so setting a new value updates in place rather than
    creating a contradiction. Inferred self-beliefs do not belong here —
    they go through the normal extraction path as model_inferred facts.
    """

    def __init__(self, engine: MnemeMemory, *, subject: str = SELF_SUBJECT) -> None:
        self.engine = engine
        self.subject = subject

    def set_identity_fact(
        self,
        predicate: str,
        value: Any,
        *,
        source_type: SourceType | str = SourceType.SYSTEM_GENERATED,
        confidence: float = 0.9,
        notes: str | None = None,
    ) -> Fact:
        fact = Fact(
            fact_id=f"fact_self_{_slug(predicate)}",
            subject=self.subject,
            predicate=predicate,
            object_value={"value": value},
            confidence=confidence,
            source_type=parse_source_type(source_type),
        )
        result = self.engine.add_fact(
            fact,
            source_id=self.subject,
            derivation_path=["self_model", "identity", "fact"],
            notes=notes,
        )
        return result.fact

    def get_identity(self, predicate: str) -> Fact | None:
        return self.engine.store.get_fact(f"fact_self_{_slug(predicate)}")

    def identity_facts(self) -> list[Fact]:
        facts = self.engine.store.search_facts_structured(
            subject=self.subject,
            status=MemoryStatus.ACTIVE,
            limit=100,
        )
        identity = [
            fact
            for fact in facts
            if fact.subject == self.subject
            and not fact.predicate.startswith(PROCEDURE_PREDICATE_PREFIX)
        ]
        return sorted(identity, key=lambda fact: fact.predicate)

    def describe(self) -> str:
        facts = self.identity_facts()
        if not facts:
            return "self model is empty"
        parts = [
            f"{fact.predicate}: {fact.object_value.get('value')}"
            for fact in facts
        ]
        return "; ".join(parts)


class ProceduralMemory:
    """Versioned skill parameters with provenance (procedural memory v0).

    Storage only — parameters change exclusively through explicit
    set_parameter calls. Autonomous procedural learning is a Stage 7
    concern and is deliberately not implemented here.
    """

    def __init__(self, engine: MnemeMemory, *, subject: str = SELF_SUBJECT) -> None:
        self.engine = engine
        self.subject = subject

    def set_parameter(
        self,
        skill: str,
        parameter: str,
        value: Any,
        *,
        confidence: float = 0.9,
        reason: str | None = None,
    ) -> Fact:
        predicate = f"{PROCEDURE_PREDICATE_PREFIX}{skill}:{parameter}"
        current = self._latest_version(skill, parameter)
        version = (current.object_value["version"] + 1) if current is not None else 1
        fact = Fact(
            fact_id=f"fact_proc_{_slug(skill)}_{_slug(parameter)}_v{version}",
            subject=self.subject,
            predicate=predicate,
            object_value={
                "value": value,
                "version": version,
                "skill": skill,
                "parameter": parameter,
            },
            confidence=confidence,
            source_type=SourceType.SYSTEM_GENERATED,
            supersedes_fact_id=current.fact_id if current is not None else None,
        )
        result = self.engine.add_fact(
            fact,
            source_id=self.subject,
            derivation_path=["self_model", "procedural", "fact"],
            notes=reason,
        )
        if current is not None:
            self.engine.store.set_fact_status(current.fact_id, MemoryStatus.SUPERSEDED)
        return result.fact

    def get_parameter(self, skill: str, parameter: str, *, default: Any = None) -> Any:
        current = self._latest_version(skill, parameter, active_only=True)
        if current is None:
            return default
        return current.object_value["value"]

    def parameter_history(self, skill: str, parameter: str) -> list[Fact]:
        facts = self._all_versions(skill, parameter)
        return sorted(facts, key=lambda fact: fact.object_value["version"])

    def parameters_for_skill(self, skill: str) -> dict[str, Any]:
        prefix = f"{PROCEDURE_PREDICATE_PREFIX}{skill}:"
        facts = self.engine.store.search_facts_structured(
            predicate=prefix,
            status=MemoryStatus.ACTIVE,
            limit=200,
        )
        return {
            fact.object_value["parameter"]: fact.object_value["value"]
            for fact in facts
            if fact.predicate.startswith(prefix)
        }

    def _all_versions(self, skill: str, parameter: str) -> list[Fact]:
        predicate = f"{PROCEDURE_PREDICATE_PREFIX}{skill}:{parameter}"
        facts = self.engine.store.search_facts_structured(
            predicate=predicate,
            status=None,
            limit=200,
        )
        return [fact for fact in facts if fact.predicate == predicate]

    def _latest_version(
        self,
        skill: str,
        parameter: str,
        *,
        active_only: bool = False,
    ) -> Fact | None:
        versions = self._all_versions(skill, parameter)
        if active_only:
            versions = [fact for fact in versions if fact.status == MemoryStatus.ACTIVE]
        if not versions:
            return None
        return max(versions, key=lambda fact: fact.object_value["version"])
