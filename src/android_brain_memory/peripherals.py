from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
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


class RealPeripheralBackend(PeripheralDiscoveryBackend):
    """Best-effort host peripheral discovery without optional runtime dependencies.

    The backend inventories devices only. It does not open cameras, record audio,
    play audio, or request sensor streams.
    """

    def __init__(
        self,
        *,
        platform_name: str | None = None,
        command_runner: Callable[[Sequence[str], int], str] | None = None,
        timeout_ms: int = 1_500,
    ) -> None:
        self.platform_name = platform_name or platform.system()
        self.command_runner = command_runner or _run_command
        self.timeout_ms = _positive_int(timeout_ms, "timeout_ms")

    def scan(self) -> list[PeripheralDevice]:
        system = self.platform_name.lower()
        if system == "darwin":
            devices = self._scan_macos()
        elif system == "linux":
            devices = self._scan_linux()
        elif system == "windows":
            devices = self._scan_windows()
        else:
            devices = []
        return _dedupe_devices(devices)

    def _scan_macos(self) -> list[PeripheralDevice]:
        output = self._try_command([
            "system_profiler",
            "-json",
            "SPCameraDataType",
            "SPAudioDataType",
        ])
        if not output:
            return []
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return []

        devices: list[PeripheralDevice] = []
        for item in _as_list(data.get("SPCameraDataType")):
            label = _label_from_mapping(item)
            if label:
                devices.append(self._device(PeripheralKind.CAMERA, label, item, "system_profiler"))

        for item in _walk_mappings(data.get("SPAudioDataType")):
            label = _label_from_mapping(item)
            if not label:
                continue
            text = " ".join(str(value).lower() for value in item.values())
            keys = " ".join(str(key).lower() for key in item)
            if "input" in text or "microphone" in text or "input" in keys:
                devices.append(self._device(PeripheralKind.MICROPHONE, label, item, "system_profiler"))
            if "output" in text or "speaker" in text or "output" in keys:
                devices.append(self._device(PeripheralKind.SPEAKER, label, item, "system_profiler"))
        return devices

    def _scan_linux(self) -> list[PeripheralDevice]:
        devices: list[PeripheralDevice] = []
        devices.extend(self._linux_cameras())
        devices.extend(self._linux_audio(["arecord", "-l"], PeripheralKind.MICROPHONE, "arecord"))
        devices.extend(self._linux_audio(["aplay", "-l"], PeripheralKind.SPEAKER, "aplay"))
        devices.extend(self._linux_pactl(["pactl", "list", "short", "sources"], PeripheralKind.MICROPHONE))
        devices.extend(self._linux_pactl(["pactl", "list", "short", "sinks"], PeripheralKind.SPEAKER))
        return devices

    def _scan_windows(self) -> list[PeripheralDevice]:
        script = (
            "Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.PNPClass -in @('Camera','Image','AudioEndpoint','Media') } | "
            "Select-Object Name,DeviceID,PNPClass,Status | ConvertTo-Json -Depth 3"
        )
        output = self._try_command([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ])
        if not output:
            return []
        try:
            rows = _as_list(json.loads(output))
        except json.JSONDecodeError:
            return []

        devices: list[PeripheralDevice] = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            label = _label_from_mapping(row)
            if not label:
                continue
            pnp_class = str(row.get("PNPClass", "")).lower()
            lowered = label.lower()
            if pnp_class in {"camera", "image"} or "camera" in lowered or "webcam" in lowered:
                devices.append(self._device(PeripheralKind.CAMERA, label, row, "powershell"))
            elif "microphone" in lowered or "input" in lowered:
                devices.append(self._device(PeripheralKind.MICROPHONE, label, row, "powershell"))
            elif "speaker" in lowered or "output" in lowered or "audio" in lowered:
                devices.append(self._device(PeripheralKind.SPEAKER, label, row, "powershell"))
        return devices

    def _linux_cameras(self) -> list[PeripheralDevice]:
        output = self._try_command(["v4l2-ctl", "--list-devices"])
        if not output:
            return []
        devices: list[PeripheralDevice] = []
        current_label: str | None = None
        current_paths: list[str] = []
        for raw in output.splitlines() + [""]:
            line = raw.rstrip()
            if not line:
                if current_label:
                    metadata = {"paths": list(current_paths), "source": "v4l2-ctl"}
                    devices.append(self._device(PeripheralKind.CAMERA, current_label, metadata, "v4l2-ctl"))
                current_label = None
                current_paths = []
                continue
            if line.startswith("\t") or line.startswith(" "):
                path = line.strip()
                if path:
                    current_paths.append(path)
            else:
                current_label = line.rstrip(":")
        return devices

    def _linux_audio(
        self,
        command: Sequence[str],
        kind: PeripheralKind,
        source: str,
    ) -> list[PeripheralDevice]:
        output = self._try_command(command)
        if not output:
            return []
        devices: list[PeripheralDevice] = []
        pattern = re.compile(r"card\s+(?P<card>\d+):\s*(?P<card_name>[^,]+),\s*device\s+(?P<device>\d+):\s*(?P<label>.+)")
        for line in output.splitlines():
            match = pattern.search(line)
            if not match:
                continue
            label = match.group("label").strip()
            metadata = {
                "card": match.group("card"),
                "card_name": match.group("card_name").strip(),
                "device": match.group("device"),
                "source": source,
            }
            devices.append(self._device(kind, label, metadata, source))
        return devices

    def _linux_pactl(self, command: Sequence[str], kind: PeripheralKind) -> list[PeripheralDevice]:
        output = self._try_command(command)
        if not output:
            return []
        devices: list[PeripheralDevice] = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            label = parts[1].strip()
            if label.endswith(".monitor"):
                continue
            devices.append(
                self._device(
                    kind,
                    label,
                    {"index": parts[0].strip(), "source": "pactl"},
                    "pactl",
                )
            )
        return devices

    def _try_command(self, command: Sequence[str]) -> str | None:
        try:
            return self.command_runner(command, self.timeout_ms)
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            return None

    def _device(
        self,
        kind: PeripheralKind,
        label: str,
        raw: Mapping[str, Any],
        source: str,
    ) -> PeripheralDevice:
        metadata = {
            "backend": "real",
            "platform": self.platform_name,
            "source": source,
        }
        raw_id = raw.get("device_id") or raw.get("DeviceID") or raw.get("unique_id")
        if raw_id:
            metadata["native_id"] = str(raw_id)
        return PeripheralDevice(
            device_id=_fingerprint(kind.value, str(raw_id or label)),
            kind=kind,
            label=label,
            available=True,
            confidence=0.8,
            metadata=metadata,
        )


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


def default_host_peripheral_backend() -> RealPeripheralBackend:
    return RealPeripheralBackend()


def _run_command(command: Sequence[str], timeout_ms: int) -> str:
    completed = subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_ms / 1000,
    )
    return completed.stdout


def _dedupe_devices(devices: Sequence[PeripheralDevice]) -> list[PeripheralDevice]:
    seen: set[tuple[str, str]] = set()
    unique: list[PeripheralDevice] = []
    for device in devices:
        key = (device.kind.value, device.device_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(device)
    return sorted(unique, key=lambda item: (item.kind.value, item.label, item.device_id))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _walk_mappings(value: Any) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        found.append(value)
        for child in value.values():
            found.extend(_walk_mappings(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_mappings(item))
    return found


def _label_from_mapping(value: Mapping[str, Any]) -> str | None:
    for key in ("_name", "Name", "name", "label", "device_name"):
        label = value.get(key)
        if isinstance(label, str) and label.strip():
            clean = label.strip()
            if clean.lower() in {"coreaudio_device"}:
                continue
            return clean
    return None


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
