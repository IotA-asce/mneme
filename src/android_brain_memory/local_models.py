from __future__ import annotations

import hashlib
import shutil
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_REGISTRY = ROOT / "config" / "models.yaml"
DEFAULT_MODEL_DIR = ROOT / ".local" / "models"


@dataclass(slots=True)
class LocalModelRecord:
    model_id: str
    backend: str
    path: Path | str
    license: str
    profiles: list[str] = field(default_factory=list)
    description: str = ""
    source_url: str | None = None
    download_url: str | None = None
    sha256: str | None = None
    required: bool = False

    def __post_init__(self) -> None:
        self.model_id = _required_text(self.model_id, "model_id")
        self.backend = _required_text(self.backend, "backend")
        self.path = Path(_required_text(str(self.path), "path"))
        self.license = _required_text(self.license, "license")
        self.profiles = _string_list(self.profiles, "profiles")
        self.description = str(self.description or "")
        self.source_url = _optional_text(self.source_url, "source_url")
        self.download_url = _optional_text(self.download_url, "download_url")
        self.sha256 = _optional_text(self.sha256, "sha256")
        if not isinstance(self.required, bool):
            raise ValueError("required must be a boolean")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], *, base_dir: Path = ROOT) -> "LocalModelRecord":
        item = dict(data)
        raw_path = _required_text(str(item.get("path", "")), "path")
        path = Path(raw_path)
        if not path.is_absolute():
            path = base_dir / path
        return cls(
            model_id=item.get("model_id", item.get("id")),
            backend=item.get("backend"),
            path=path,
            license=item.get("license"),
            profiles=list(item.get("profiles", [])),
            description=str(item.get("description", "")),
            source_url=item.get("source_url"),
            download_url=item.get("download_url"),
            sha256=item.get("sha256"),
            required=bool(item.get("required", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "backend": self.backend,
            "path": str(self.path),
            "license": self.license,
            "profiles": list(self.profiles),
            "description": self.description,
            "source_url": self.source_url,
            "download_url": self.download_url,
            "sha256": self.sha256,
            "required": self.required,
        }


@dataclass(slots=True)
class ModelVerification:
    model_id: str
    path: str
    exists: bool
    checksum_ok: bool | None = None
    actual_sha256: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "path": self.path,
            "exists": self.exists,
            "checksum_ok": self.checksum_ok,
            "actual_sha256": self.actual_sha256,
            "error": self.error,
        }


class LocalModelRegistry:
    def __init__(
        self,
        records: Sequence[LocalModelRecord] | None = None,
        *,
        registry_path: str | Path = DEFAULT_MODEL_REGISTRY,
        model_dir: str | Path = DEFAULT_MODEL_DIR,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.model_dir = Path(model_dir)
        self.records = list(records) if records is not None else self._load_records()

    def list_models(self, *, profile: str | None = None) -> list[LocalModelRecord]:
        if profile is None:
            return sorted(self.records, key=lambda item: item.model_id)
        return sorted(
            [record for record in self.records if profile in record.profiles],
            key=lambda item: item.model_id,
        )

    def get(self, model_id: str) -> LocalModelRecord:
        clean_id = _required_text(model_id, "model_id")
        for record in self.records:
            if record.model_id == clean_id:
                return record
        raise KeyError(f"unknown model id: {clean_id}")

    def verify(self, model_id: str | None = None) -> list[ModelVerification]:
        records = [self.get(model_id)] if model_id else self.list_models()
        return [self._verify_record(record) for record in records]

    def download(self, model_id: str, *, overwrite: bool = False) -> LocalModelRecord:
        record = self.get(model_id)
        if not record.download_url:
            raise ValueError(f"download is not configured for {record.model_id}")
        if record.path.exists() and not overwrite:
            return record
        record.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = record.path.with_suffix(f"{record.path.suffix}.tmp")
        with urllib.request.urlopen(record.download_url, timeout=60) as response:
            with tmp_path.open("wb") as target:
                shutil.copyfileobj(response, target)
        tmp_path.replace(record.path)
        verification = self._verify_record(record)
        if verification.checksum_ok is False:
            raise ValueError(f"checksum mismatch for {record.model_id}")
        return record

    def to_dict(self, *, profile: str | None = None) -> dict[str, Any]:
        return {
            "registry_path": str(self.registry_path),
            "model_dir": str(self.model_dir),
            "models": [record.to_dict() for record in self.list_models(profile=profile)],
        }

    def _load_records(self) -> list[LocalModelRecord]:
        if not self.registry_path.exists():
            return []
        data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
        raw_models = data.get("models", [])
        if not isinstance(raw_models, list):
            raise ValueError("models registry must contain a models list")
        return [LocalModelRecord.from_dict(item) for item in raw_models]

    def _verify_record(self, record: LocalModelRecord) -> ModelVerification:
        if not record.path.exists():
            return ModelVerification(
                model_id=record.model_id,
                path=str(record.path),
                exists=False,
                error="missing",
            )
        if record.path.is_dir():
            return ModelVerification(
                model_id=record.model_id,
                path=str(record.path),
                exists=True,
                checksum_ok=None,
            )
        actual = _sha256(record.path)
        expected = record.sha256
        return ModelVerification(
            model_id=record.model_id,
            path=str(record.path),
            exists=True,
            checksum_ok=(actual == expected) if expected else None,
            actual_sha256=actual,
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None


def _string_list(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must be a list of strings")
    return items
