from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_PREFERENCES = Path(".local/runtime_preferences.json")
_UNSET = object()


@dataclass(slots=True)
class RuntimeDevicePreferences:
    camera_device_id: str | None = None
    microphone_device_id: str | None = None
    speaker_device_id: str | None = None

    def __post_init__(self) -> None:
        self.camera_device_id = _optional_text(self.camera_device_id, "camera_device_id")
        self.microphone_device_id = _optional_text(self.microphone_device_id, "microphone_device_id")
        self.speaker_device_id = _optional_text(self.speaker_device_id, "speaker_device_id")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "RuntimeDevicePreferences":
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            raise ValueError("runtime device preferences must be a mapping")
        return cls(
            camera_device_id=data.get("camera_device_id"),
            microphone_device_id=data.get("microphone_device_id"),
            speaker_device_id=data.get("speaker_device_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera_device_id": self.camera_device_id,
            "microphone_device_id": self.microphone_device_id,
            "speaker_device_id": self.speaker_device_id,
        }

    def merged(
        self,
        *,
        camera_device_id: str | None = None,
        microphone_device_id: str | None = None,
        speaker_device_id: str | None = None,
    ) -> "RuntimeDevicePreferences":
        return RuntimeDevicePreferences(
            camera_device_id=(
                _optional_text(camera_device_id, "camera_device_id")
                if camera_device_id is not None
                else self.camera_device_id
            ),
            microphone_device_id=(
                _optional_text(microphone_device_id, "microphone_device_id")
                if microphone_device_id is not None
                else self.microphone_device_id
            ),
            speaker_device_id=(
                _optional_text(speaker_device_id, "speaker_device_id")
                if speaker_device_id is not None
                else self.speaker_device_id
            ),
        )


class RuntimePreferencesStore:
    def __init__(self, path: str | Path = DEFAULT_RUNTIME_PREFERENCES) -> None:
        self.path = Path(path)

    def load(self) -> RuntimeDevicePreferences:
        if not self.path.exists():
            return RuntimeDevicePreferences()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid runtime preferences file: {self.path}") from exc
        return RuntimeDevicePreferences.from_dict(data.get("devices") if isinstance(data, Mapping) else data)

    def save(self, preferences: RuntimeDevicePreferences | Mapping[str, Any]) -> RuntimeDevicePreferences:
        prefs = (
            preferences
            if isinstance(preferences, RuntimeDevicePreferences)
            else RuntimeDevicePreferences.from_dict(preferences)
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"devices": prefs.to_dict()}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return prefs

    def update(
        self,
        *,
        camera_device_id: str | None | object = _UNSET,
        microphone_device_id: str | None | object = _UNSET,
        speaker_device_id: str | None | object = _UNSET,
    ) -> RuntimeDevicePreferences:
        current = self.load()
        updated = RuntimeDevicePreferences(
            camera_device_id=(
                current.camera_device_id
                if camera_device_id is _UNSET
                else _optional_text(camera_device_id, "camera_device_id")
            ),
            microphone_device_id=(
                current.microphone_device_id
                if microphone_device_id is _UNSET
                else _optional_text(microphone_device_id, "microphone_device_id")
            ),
            speaker_device_id=(
                current.speaker_device_id
                if speaker_device_id is _UNSET
                else _optional_text(speaker_device_id, "speaker_device_id")
            ),
        )
        return self.save(updated)


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None
