from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .models import validate_confidence, validate_timestamp
from .runtime import EventBus, world_state_update


DEFAULT_DISCOVERY_INTERVAL_MS = 5_000


class PeripheralKind(StrEnum):
    CAMERA = "camera"
    MICROPHONE = "microphone"
    SPEAKER = "speaker"


@dataclass(slots=True)
class PeripheralDevice:
    device_id: str
    kind: PeripheralKind | str
    label: str
    available: bool = True
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.kind = self.kind if isinstance(self.kind, PeripheralKind) else PeripheralKind(self.kind)
        self.label = _required_text(self.label, "label")
        if self.device_id is None or not isinstance(self.device_id, str) or not self.device_id.strip():
            self.device_id = _fingerprint(self.kind.value, self.label)
        else:
            self.device_id = _required_text(self.device_id, "device_id")
        if not isinstance(self.available, bool):
            raise ValueError("available must be a boolean")
        self.confidence = validate_confidence(self.confidence)
        self.metadata = _json_mapping(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "kind": self.kind.value,
            "label": self.label,
            "available": self.available,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PeripheralDevice":
        data = _required_mapping(data)
        return cls(
            device_id=data.get("device_id", ""),
            kind=data.get("kind"),
            label=data.get("label"),
            available=data.get("available", True),
            confidence=data.get("confidence", 1.0),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(slots=True)
class PeripheralSnapshot:
    snapshot_id: str
    scanned_ts: int
    devices: list[PeripheralDevice] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.snapshot_id = _required_text(self.snapshot_id, "snapshot_id")
        self.scanned_ts = validate_timestamp(self.scanned_ts, "scanned_ts")
        self.devices = [
            device if isinstance(device, PeripheralDevice) else PeripheralDevice.from_dict(device)
            for device in self.devices
        ]

    def available(self, kind: PeripheralKind | str) -> list[PeripheralDevice]:
        parsed = kind if isinstance(kind, PeripheralKind) else PeripheralKind(kind)
        return [device for device in self.devices if device.kind == parsed and device.available]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "scanned_ts": self.scanned_ts,
            "devices": [device.to_dict() for device in self.devices],
            "available_counts": {
                kind.value: len(self.available(kind))
                for kind in PeripheralKind
            },
        }


class PeripheralDiscoveryBackend:
    """Backend interface for device discovery."""

    def scan(self) -> list[PeripheralDevice]:
        raise NotImplementedError


class FakePeripheralBackend(PeripheralDiscoveryBackend):
    """Deterministic fake discovery backend for tests and CI."""

    def __init__(self, devices: Sequence[PeripheralDevice | Mapping[str, Any]] | None = None) -> None:
        self._devices = [
            device if isinstance(device, PeripheralDevice) else PeripheralDevice.from_dict(device)
            for device in (devices or [])
        ]

    def set_devices(self, devices: Sequence[PeripheralDevice | Mapping[str, Any]]) -> None:
        self._devices = [
            device if isinstance(device, PeripheralDevice) else PeripheralDevice.from_dict(device)
            for device in devices
        ]

    def scan(self) -> list[PeripheralDevice]:
        return [PeripheralDevice.from_dict(device.to_dict()) for device in self._devices]


class PeripheralDiscoveryService:
    """Publishes discovered host peripherals as world state.

    V0 ships with a fake backend only. Real platform backends can later
    implement the same scan() contract without changing runtime wiring.
    """

    def __init__(
        self,
        *,
        backend: PeripheralDiscoveryBackend | None = None,
        bus: EventBus | None = None,
        source: str = "peripheral_discovery",
        scan_interval_ms: int = DEFAULT_DISCOVERY_INTERVAL_MS,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.backend = backend or FakePeripheralBackend()
        self.bus = bus
        self.source = _required_text(source, "source")
        self.scan_interval_ms = _positive_int(scan_interval_ms, "scan_interval_ms")
        self._clock = clock or _now_ms
        self._last_scan_ms: int | None = None
        self._scan_counter = 0
        self._last_snapshot: PeripheralSnapshot | None = None

    @property
    def last_snapshot(self) -> PeripheralSnapshot | None:
        return self._last_snapshot

    def scan_now(self, *, now_ms: int | None = None, publish: bool = True) -> PeripheralSnapshot:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self._scan_counter += 1
        snapshot = PeripheralSnapshot(
            snapshot_id=f"peripheral_scan_{self._scan_counter:06d}",
            scanned_ts=now,
            devices=sorted(
                self.backend.scan(),
                key=lambda device: (device.kind.value, device.device_id),
            ),
        )
        self._last_snapshot = snapshot
        self._last_scan_ms = now
        if publish:
            self._publish_snapshot(snapshot)
        return snapshot

    def tick(self, *, now_ms: int | None = None) -> PeripheralSnapshot | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._last_scan_ms is not None and now - self._last_scan_ms < self.scan_interval_ms:
            return None
        return self.scan_now(now_ms=now)

    def _publish_snapshot(self, snapshot: PeripheralSnapshot) -> None:
        if self.bus is None:
            return
        payload = snapshot.to_dict()
        self.bus.publish(
            world_state_update(
                source=self.source,
                state_key="peripheral_inventory",
                payload={"value": payload, **payload},
                confidence=1.0,
                timestamp=snapshot.scanned_ts,
            )
        )


def default_virtual_head_devices() -> list[PeripheralDevice]:
    return [
        PeripheralDevice(device_id="fake_camera_001", kind=PeripheralKind.CAMERA, label="Fake Camera"),
        PeripheralDevice(device_id="fake_mic_001", kind=PeripheralKind.MICROPHONE, label="Fake Microphone"),
        PeripheralDevice(device_id="fake_speaker_001", kind=PeripheralKind.SPEAKER, label="Fake Speaker"),
    ]


def _fingerprint(kind: str, label: str) -> str:
    digest = hashlib.sha256(f"{kind}:{label}".encode("utf-8")).hexdigest()[:12]
    return f"{kind}_{digest}"


def _required_mapping(value: Any, field_name: str = "data") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
