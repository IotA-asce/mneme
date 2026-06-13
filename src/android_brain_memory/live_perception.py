from __future__ import annotations

import hashlib
import json
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import MemoryCandidate, SalienceFeatures, SourceType, validate_confidence, validate_timestamp
from .peripherals import PeripheralDevice, PeripheralDiscoveryService, PeripheralKind
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    memory_candidate_event,
    memory_lifecycle_event,
    perception_observation,
    world_state_update,
)
from .storage import MemoryStore


DEFAULT_PERCEPTION_TTL_MS = 5_000
DEFAULT_LIVE_CAPTURE_INTERVAL_MS = 1_000
DEFAULT_MAX_ARCHIVED_FRAMES = 1_000
DEFAULT_MAX_FRAME_ARCHIVE_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_FRAME_AGE_MS = 7 * 24 * 60 * 60 * 1000


@dataclass(slots=True)
class PerceptionRetentionPolicy:
    frame_archive_dir: Path | str = Path(".local/perception_frames")
    max_archived_frames: int = DEFAULT_MAX_ARCHIVED_FRAMES
    max_frame_archive_bytes: int = DEFAULT_MAX_FRAME_ARCHIVE_BYTES
    max_frame_age_ms: int = DEFAULT_MAX_FRAME_AGE_MS
    persist_raw_frames: bool = True
    persist_transcripts: bool = True

    def __post_init__(self) -> None:
        self.frame_archive_dir = Path(self.frame_archive_dir)
        self.max_archived_frames = _positive_int(self.max_archived_frames, "max_archived_frames")
        self.max_frame_archive_bytes = _positive_int(
            self.max_frame_archive_bytes,
            "max_frame_archive_bytes",
        )
        self.max_frame_age_ms = _positive_int(self.max_frame_age_ms, "max_frame_age_ms")
        if not isinstance(self.persist_raw_frames, bool):
            raise ValueError("persist_raw_frames must be a boolean")
        if not isinstance(self.persist_transcripts, bool):
            raise ValueError("persist_transcripts must be a boolean")

    def frame_path(self, *, frame_id: str, timestamp: int, suffix: str = ".jpg") -> Path:
        validate_timestamp(timestamp, "timestamp")
        clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        return self.frame_archive_dir / f"{timestamp}_{_safe_id(frame_id)}{clean_suffix}"

    def enforce_frame_archive(self, *, now_ms: int | None = None) -> dict[str, Any]:
        now = _now_ms() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self.frame_archive_dir.mkdir(parents=True, exist_ok=True)
        files = [
            path
            for path in self.frame_archive_dir.iterdir()
            if path.is_file() and not path.name.endswith(".json")
        ]
        removed: list[str] = []
        cutoff_s = (now - self.max_frame_age_ms) / 1000
        for path in list(files):
            if path.stat().st_mtime < cutoff_s:
                _unlink(path)
                removed.append(str(path))
                files.remove(path)

        files.sort(key=lambda path: path.stat().st_mtime)
        while len(files) > self.max_archived_frames:
            path = files.pop(0)
            _unlink(path)
            removed.append(str(path))

        total_bytes = sum(path.stat().st_size for path in files if path.exists())
        while total_bytes > self.max_frame_archive_bytes and files:
            path = files.pop(0)
            size = path.stat().st_size if path.exists() else 0
            _unlink(path)
            removed.append(str(path))
            total_bytes -= size

        return {
            "archive_dir": str(self.frame_archive_dir),
            "archived_frames": len(files),
            "archive_bytes": max(total_bytes, 0),
            "removed_count": len(removed),
            "removed": removed,
            "limits": self.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_archive_dir": str(self.frame_archive_dir),
            "max_archived_frames": self.max_archived_frames,
            "max_frame_archive_bytes": self.max_frame_archive_bytes,
            "max_frame_age_ms": self.max_frame_age_ms,
            "persist_raw_frames": self.persist_raw_frames,
            "persist_transcripts": self.persist_transcripts,
        }


@dataclass(slots=True)
class CapturedFrame:
    frame_id: str
    captured_ts: int
    device_id: str
    device_label: str
    path: Path | str
    mime_type: str
    size_bytes: int
    sha256: str
    confidence: float = 0.8
    detections: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frame_id = _required_text(self.frame_id, "frame_id")
        self.captured_ts = validate_timestamp(self.captured_ts, "captured_ts")
        self.device_id = _required_text(self.device_id, "device_id")
        self.device_label = _required_text(self.device_label, "device_label")
        self.path = Path(self.path)
        self.mime_type = _required_text(self.mime_type, "mime_type")
        self.size_bytes = _non_negative_int(self.size_bytes, "size_bytes")
        self.sha256 = _required_text(self.sha256, "sha256")
        self.confidence = validate_confidence(self.confidence)
        self.detections = _mapping_list(self.detections, "detections")
        self.metadata = _json_mapping(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "captured_ts": self.captured_ts,
            "device_id": self.device_id,
            "device_label": self.device_label,
            "path": str(self.path),
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "confidence": self.confidence,
            "detections": [dict(item) for item in self.detections],
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class SpeechTranscriptObservation:
    transcript_id: str
    captured_ts: int
    device_id: str
    device_label: str
    speaker: str
    transcript: str
    confidence: float
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.transcript_id = _required_text(self.transcript_id, "transcript_id")
        self.captured_ts = validate_timestamp(self.captured_ts, "captured_ts")
        self.device_id = _required_text(self.device_id, "device_id")
        self.device_label = _required_text(self.device_label, "device_label")
        self.speaker = _required_text(self.speaker, "speaker")
        self.transcript = _required_text(self.transcript, "transcript")
        self.confidence = validate_confidence(self.confidence)
        if self.duration_ms is not None:
            self.duration_ms = _positive_int(self.duration_ms, "duration_ms")
        self.metadata = _json_mapping(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcript_id": self.transcript_id,
            "captured_ts": self.captured_ts,
            "device_id": self.device_id,
            "device_label": self.device_label,
            "speaker": self.speaker,
            "transcript": self.transcript,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class LivePerceptionReport:
    worker: str
    timestamp: int
    status: str
    device_id: str | None = None
    trace_id: str | None = None
    event_ids: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.worker = _required_text(self.worker, "worker")
        self.timestamp = validate_timestamp(self.timestamp, "timestamp")
        self.status = _required_text(self.status, "status")
        if self.device_id is not None:
            self.device_id = _required_text(self.device_id, "device_id")
        self.event_ids = _string_list(self.event_ids, "event_ids")
        self.details = _json_mapping(self.details, "details")

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker": self.worker,
            "timestamp": self.timestamp,
            "status": self.status,
            "device_id": self.device_id,
            "trace_id": self.trace_id,
            "event_ids": list(self.event_ids),
            "details": dict(self.details),
        }


class CameraCaptureBackend:
    def capture(
        self,
        *,
        device: PeripheralDevice,
        output_path: Path,
        timestamp: int,
    ) -> CapturedFrame | None:
        raise NotImplementedError


class SpeechRecognitionBackend:
    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        raise NotImplementedError


class NoopCameraCaptureBackend(CameraCaptureBackend):
    def capture(
        self,
        *,
        device: PeripheralDevice,
        output_path: Path,
        timestamp: int,
    ) -> CapturedFrame | None:
        return None


class NoopSpeechRecognitionBackend(SpeechRecognitionBackend):
    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        return None


class ScriptedCameraCaptureBackend(CameraCaptureBackend):
    """Deterministic backend used by tests and replay demos."""

    def __init__(self, frames: Sequence[bytes | Mapping[str, Any]]) -> None:
        self._frames = list(frames)
        self._index = 0

    def capture(
        self,
        *,
        device: PeripheralDevice,
        output_path: Path,
        timestamp: int,
    ) -> CapturedFrame | None:
        if self._index >= len(self._frames):
            return None
        item = self._frames[self._index]
        self._index += 1
        data: bytes
        detections: list[dict[str, Any]]
        metadata: dict[str, Any]
        mime_type = "image/jpeg"
        suffix = output_path.suffix
        if isinstance(item, Mapping):
            content = item.get("content", b"mneme-frame")
            data = content if isinstance(content, bytes) else str(content).encode("utf-8")
            detections = _mapping_list(item.get("detections", []), "detections")
            metadata = dict(item.get("metadata", {}))
            mime_type = str(item.get("mime_type", mime_type))
            suffix = str(item.get("suffix", suffix))
        else:
            data = bytes(item)
            detections = []
            metadata = {}
        if suffix and output_path.suffix != suffix:
            output_path = output_path.with_suffix(suffix)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        return _frame_from_file(
            frame_id=f"frame_{uuid.uuid4().hex[:12]}",
            timestamp=timestamp,
            device=device,
            path=output_path,
            mime_type=mime_type,
            confidence=float(metadata.get("confidence", 0.8)),
            detections=detections,
            metadata={"backend": "scripted", **metadata},
        )


class ScriptedSpeechRecognitionBackend(SpeechRecognitionBackend):
    """Deterministic transcript backend used by tests and replay demos."""

    def __init__(self, transcripts: Sequence[str | Mapping[str, Any]]) -> None:
        self._transcripts = list(transcripts)
        self._index = 0

    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        if self._index >= len(self._transcripts):
            return None
        item = self._transcripts[self._index]
        self._index += 1
        if isinstance(item, Mapping):
            text = _required_text(
                item.get("transcript", item.get("text")),
                "transcript",
            )
            speaker = str(item.get("speaker", "unknown_speaker"))
            confidence = float(item.get("confidence", 0.8))
            duration_ms = item.get("duration_ms")
            metadata = dict(item.get("metadata", {}))
        else:
            text = _required_text(item, "transcript")
            speaker = "unknown_speaker"
            confidence = 0.8
            duration_ms = None
            metadata = {}
        return SpeechTranscriptObservation(
            transcript_id=f"transcript_{uuid.uuid4().hex[:12]}",
            captured_ts=timestamp,
            device_id=device.device_id,
            device_label=device.label,
            speaker=speaker,
            transcript=text,
            confidence=confidence,
            duration_ms=duration_ms,
            metadata={"backend": "scripted", **metadata},
        )


class CommandFrameCaptureBackend(CameraCaptureBackend):
    """Runs a configured local command that writes one frame to `{output}`."""

    def __init__(
        self,
        command_template: Sequence[str],
        *,
        command_runner: Callable[[Sequence[str], int], str] | None = None,
        timeout_ms: int = 5_000,
        mime_type: str = "image/jpeg",
    ) -> None:
        self.command_template = [_required_text(part, "command_template item") for part in command_template]
        if not self.command_template:
            raise ValueError("command_template must not be empty")
        self.command_runner = command_runner or _run_command
        self.timeout_ms = _positive_int(timeout_ms, "timeout_ms")
        self.mime_type = _required_text(mime_type, "mime_type")

    def capture(
        self,
        *,
        device: PeripheralDevice,
        output_path: Path,
        timestamp: int,
    ) -> CapturedFrame | None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            _format_command_part(
                part,
                {
                    "output": str(output_path),
                    "device_id": device.device_id,
                    "label": device.label,
                },
            )
            for part in self.command_template
        ]
        stdout = self.command_runner(command, self.timeout_ms)
        if not output_path.exists() or output_path.stat().st_size == 0:
            return None
        metadata: dict[str, Any] = {"backend": "command", "command": command}
        detections: list[dict[str, Any]] = []
        parsed = _parse_json(stdout)
        if isinstance(parsed, Mapping):
            metadata["stdout_json"] = dict(parsed)
            detections = _mapping_list(parsed.get("detections", []), "detections")
        sidecar = output_path.with_suffix(f"{output_path.suffix}.json")
        if sidecar.exists():
            sidecar_data = _parse_json(sidecar.read_text(encoding="utf-8"))
            if isinstance(sidecar_data, Mapping):
                metadata["sidecar_json"] = dict(sidecar_data)
                detections.extend(_mapping_list(sidecar_data.get("detections", []), "detections"))
        return _frame_from_file(
            frame_id=f"frame_{uuid.uuid4().hex[:12]}",
            timestamp=timestamp,
            device=device,
            path=output_path,
            mime_type=self.mime_type,
            confidence=0.8,
            detections=detections,
            metadata=metadata,
        )


class CommandSpeechRecognitionBackend(SpeechRecognitionBackend):
    """Runs a configured local command and parses a transcript from stdout."""

    def __init__(
        self,
        command_template: Sequence[str],
        *,
        command_runner: Callable[[Sequence[str], int], str] | None = None,
        timeout_ms: int = 10_000,
        default_speaker: str = "unknown_speaker",
    ) -> None:
        self.command_template = [_required_text(part, "command_template item") for part in command_template]
        if not self.command_template:
            raise ValueError("command_template must not be empty")
        self.command_runner = command_runner or _run_command
        self.timeout_ms = _positive_int(timeout_ms, "timeout_ms")
        self.default_speaker = _required_text(default_speaker, "default_speaker")

    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        command = [
            _format_command_part(part, {"device_id": device.device_id, "label": device.label})
            for part in self.command_template
        ]
        stdout = self.command_runner(command, self.timeout_ms).strip()
        if not stdout:
            return None
        parsed = _parse_json(stdout)
        if isinstance(parsed, Mapping):
            transcript = parsed.get("transcript", parsed.get("text"))
            speaker = parsed.get("speaker", self.default_speaker)
            confidence = parsed.get("confidence", 0.8)
            duration_ms = parsed.get("duration_ms")
            metadata = {"backend": "command", "command": command, "stdout_json": dict(parsed)}
        else:
            transcript = stdout
            speaker = self.default_speaker
            confidence = 0.8
            duration_ms = None
            metadata = {"backend": "command", "command": command}
        return SpeechTranscriptObservation(
            transcript_id=f"transcript_{uuid.uuid4().hex[:12]}",
            captured_ts=timestamp,
            device_id=device.device_id,
            device_label=device.label,
            speaker=str(speaker),
            transcript=_required_text(transcript, "transcript"),
            confidence=confidence,
            duration_ms=duration_ms,
            metadata=metadata,
        )


class LiveVisionWorker:
    """Captures bounded keyframes and publishes camera/person observations."""

    def __init__(
        self,
        *,
        discovery: PeripheralDiscoveryService,
        backend: CameraCaptureBackend | None = None,
        bus: EventBus | None = None,
        store: MemoryStore | None = None,
        retention: PerceptionRetentionPolicy | None = None,
        source: str = "live.vision_worker",
        capture_interval_ms: int = DEFAULT_LIVE_CAPTURE_INTERVAL_MS,
        preferred_device_id: str | None = None,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.discovery = discovery
        self.backend = backend or NoopCameraCaptureBackend()
        self.bus = bus
        self.store = store
        self.retention = retention or PerceptionRetentionPolicy()
        self.source = _required_text(source, "source")
        self.capture_interval_ms = _positive_int(capture_interval_ms, "capture_interval_ms")
        self.preferred_device_id = _optional_text(preferred_device_id, "preferred_device_id")
        self._clock = clock or _now_ms
        self._last_capture_ms: int | None = None
        self._stats = {
            "captures": 0,
            "frames": 0,
            "raw_traces": 0,
            "person_detections": 0,
            "skipped": 0,
        }

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)

    def tick(self, *, now_ms: int | None = None) -> LivePerceptionReport | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._last_capture_ms is not None and now - self._last_capture_ms < self.capture_interval_ms:
            return None
        self._last_capture_ms = now
        return self.capture_once(now_ms=now)

    def capture_once(self, *, now_ms: int | None = None) -> LivePerceptionReport:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        device = _first_available(
            self.discovery,
            PeripheralKind.CAMERA,
            now,
            preferred_device_id=self.preferred_device_id,
        )
        if device is None:
            self._stats["skipped"] += 1
            return LivePerceptionReport("vision", now, "no_camera")
        frame_id = f"frame_{uuid.uuid4().hex[:12]}"
        frame_path = self.retention.frame_path(frame_id=frame_id, timestamp=now)
        try:
            frame = self.backend.capture(device=device, output_path=frame_path, timestamp=now)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            self._stats["skipped"] += 1
            return LivePerceptionReport(
                "vision",
                now,
                "capture_error",
                device_id=device.device_id,
                details={"error": type(exc).__name__},
            )
        if frame is None:
            self._stats["skipped"] += 1
            return LivePerceptionReport("vision", now, "no_frame", device_id=device.device_id)

        self._stats["captures"] += 1
        self._stats["frames"] += 1
        trace_id = self._store_frame(frame) if self.retention.persist_raw_frames else None
        event_ids = self._publish_frame(frame, trace_id)
        self._stats["person_detections"] += len(frame.detections)
        retention_stats = self.retention.enforce_frame_archive(now_ms=now)
        if self.bus is not None:
            event_ids.append(
                self.bus.publish(
                    memory_lifecycle_event(
                        source=self.source,
                        lifecycle_stage="perception_retention",
                        timestamp=now,
                        payload={"modality": "vision", **retention_stats},
                    )
                ).event_id
            )
        return LivePerceptionReport(
            worker="vision",
            timestamp=now,
            status="captured",
            device_id=device.device_id,
            trace_id=trace_id,
            event_ids=event_ids,
            details={"frame": frame.to_dict(), "retention": retention_stats},
        )

    def _store_frame(self, frame: CapturedFrame) -> str | None:
        if self.store is None:
            return None
        trace_id = self.store.store_raw_trace(
            summary=f"Camera frame captured from {frame.device_label}",
            payload={"frame": frame.to_dict()},
            source_type=SourceType.SENSOR_OBSERVED,
            confidence=frame.confidence,
            salience=0.35 if frame.detections else 0.2,
            source_id=frame.frame_id,
            provenance={
                "source": {"type": SourceType.SENSOR_OBSERVED.value, "id": frame.frame_id},
                "derivation_path": ["camera_capture"],
                "supporting_memory_ids": [],
                "notes": "raw frame archive keyframe",
            },
            notes="Stage 4 camera keyframe",
            created_ts=frame.captured_ts,
        )
        self._stats["raw_traces"] += 1
        return trace_id

    def _publish_frame(self, frame: CapturedFrame, trace_id: str | None) -> list[str]:
        if self.bus is None:
            return []
        event_ids: list[str] = []
        frame_payload = frame.to_dict()
        frame_payload["observation_type"] = "camera_frame"
        frame_payload["trace_id"] = trace_id
        if trace_id is not None:
            event_ids.append(
                self.bus.publish(
                    memory_lifecycle_event(
                        source=self.source,
                        lifecycle_stage="perception_storage",
                        timestamp=frame.captured_ts,
                        payload={
                            "modality": "vision",
                            "memory_kind": "raw_trace",
                            "trace_id": trace_id,
                            "frame_id": frame.frame_id,
                            "path": str(frame.path),
                        },
                    )
                ).event_id
            )
        event_ids.append(
            self.bus.publish(
                perception_observation(
                    source=self.source,
                    observation_type="camera_frame",
                    payload=frame_payload,
                    confidence=frame.confidence,
                    timestamp=frame.captured_ts,
                    ttl_ms=DEFAULT_PERCEPTION_TTL_MS,
                    event_id=f"evt_{frame.frame_id}",
                )
            ).event_id
        )
        for index, detection in enumerate(frame.detections):
            person_id = str(detection.get("person_id", detection.get("label", f"person_{index}")))
            payload = {
                "person_id": person_id,
                "label": str(detection.get("label", person_id)),
                "observation_type": "person_seen",
                "frame_id": frame.frame_id,
                "trace_id": trace_id,
                **dict(detection),
            }
            event_ids.append(
                self.bus.publish(
                    perception_observation(
                        source=self.source,
                        observation_type="person_seen",
                        payload=payload,
                        confidence=float(detection.get("confidence", frame.confidence)),
                        timestamp=frame.captured_ts,
                        ttl_ms=DEFAULT_PERCEPTION_TTL_MS,
                        event_id=f"evt_{frame.frame_id}_person_{index}",
                    )
                ).event_id
            )
        if frame.detections:
            candidate = _vision_candidate(frame, trace_id)
            event_ids.append(
                self.bus.publish(
                    memory_candidate_event(
                        source=self.source,
                        candidate=candidate,
                        timestamp=frame.captured_ts,
                        ttl_ms=DEFAULT_PERCEPTION_TTL_MS,
                        event_id=f"evt_{candidate.candidate_id}",
                    )
                ).event_id
            )
        return event_ids


class LiveSpeechWorker:
    """Runs local speech recognition backend and publishes transcript observations."""

    def __init__(
        self,
        *,
        discovery: PeripheralDiscoveryService,
        backend: SpeechRecognitionBackend | None = None,
        bus: EventBus | None = None,
        store: MemoryStore | None = None,
        retention: PerceptionRetentionPolicy | None = None,
        source: str = "live.speech_worker",
        capture_interval_ms: int = DEFAULT_LIVE_CAPTURE_INTERVAL_MS,
        preferred_device_id: str | None = None,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.discovery = discovery
        self.backend = backend or NoopSpeechRecognitionBackend()
        self.bus = bus
        self.store = store
        self.retention = retention or PerceptionRetentionPolicy()
        self.source = _required_text(source, "source")
        self.capture_interval_ms = _positive_int(capture_interval_ms, "capture_interval_ms")
        self.preferred_device_id = _optional_text(preferred_device_id, "preferred_device_id")
        self._clock = clock or _now_ms
        self._last_capture_ms: int | None = None
        self._stats = {
            "captures": 0,
            "transcripts": 0,
            "raw_traces": 0,
            "memory_candidates": 0,
            "skipped": 0,
        }

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)

    def tick(self, *, now_ms: int | None = None) -> LivePerceptionReport | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._last_capture_ms is not None and now - self._last_capture_ms < self.capture_interval_ms:
            return None
        self._last_capture_ms = now
        return self.transcribe_once(now_ms=now)

    def transcribe_once(self, *, now_ms: int | None = None) -> LivePerceptionReport:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        device = _first_available(
            self.discovery,
            PeripheralKind.MICROPHONE,
            now,
            preferred_device_id=self.preferred_device_id,
        )
        if device is None:
            self._stats["skipped"] += 1
            return LivePerceptionReport("speech", now, "no_microphone")
        started = time.perf_counter()
        try:
            transcript = self.backend.transcribe(device=device, timestamp=now)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            self._stats["skipped"] += 1
            return LivePerceptionReport(
                "speech",
                now,
                "capture_error",
                device_id=device.device_id,
                details={
                    "error": type(exc).__name__,
                    "message": str(exc),
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                },
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if transcript is None:
            self._stats["skipped"] += 1
            return LivePerceptionReport(
                "speech",
                now,
                "no_speech",
                device_id=device.device_id,
                details={"latency_ms": latency_ms},
            )

        self._stats["captures"] += 1
        self._stats["transcripts"] += 1
        trace_id = self._store_transcript(transcript) if self.retention.persist_transcripts else None
        event_ids = self._publish_transcript(transcript, trace_id)
        return LivePerceptionReport(
            worker="speech",
            timestamp=now,
            status="transcribed",
            device_id=device.device_id,
            trace_id=trace_id,
            event_ids=event_ids,
            details={"transcript": transcript.to_dict(), "latency_ms": latency_ms},
        )

    def _store_transcript(self, transcript: SpeechTranscriptObservation) -> str | None:
        if self.store is None:
            return None
        trace_id = self.store.store_raw_trace(
            summary=f"Speech transcript from {transcript.speaker}: {_short_text(transcript.transcript)}",
            payload={"transcript": transcript.to_dict()},
            source_type=SourceType.SENSOR_OBSERVED,
            confidence=transcript.confidence,
            salience=0.55,
            source_id=transcript.transcript_id,
            provenance={
                "source": {"type": SourceType.SENSOR_OBSERVED.value, "id": transcript.transcript_id},
                "derivation_path": ["microphone_capture", "speech_recognition"],
                "supporting_memory_ids": [],
                "notes": "local speech transcript",
            },
            notes="Stage 4 speech transcript",
            created_ts=transcript.captured_ts,
        )
        self._stats["raw_traces"] += 1
        return trace_id

    def _publish_transcript(
        self,
        transcript: SpeechTranscriptObservation,
        trace_id: str | None,
    ) -> list[str]:
        if self.bus is None:
            return []
        event_ids: list[str] = []
        payload = transcript.to_dict()
        payload.update({
            "observation_type": "speech_transcript",
            "utterance": transcript.transcript,
            "trace_id": trace_id,
            "topic": _topic_for_text(transcript.transcript),
        })
        if trace_id is not None:
            event_ids.append(
                self.bus.publish(
                    memory_lifecycle_event(
                        source=self.source,
                        lifecycle_stage="perception_storage",
                        timestamp=transcript.captured_ts,
                        payload={
                            "modality": "speech",
                            "memory_kind": "raw_trace",
                            "trace_id": trace_id,
                            "transcript_id": transcript.transcript_id,
                        },
                    )
                ).event_id
            )
        event_ids.append(
            self.bus.publish(
                perception_observation(
                    source=self.source,
                    observation_type="speech_transcript",
                    payload=payload,
                    confidence=transcript.confidence,
                    timestamp=transcript.captured_ts,
                    ttl_ms=DEFAULT_PERCEPTION_TTL_MS,
                    event_id=f"evt_{transcript.transcript_id}",
                )
            ).event_id
        )
        candidate = _speech_candidate(transcript, trace_id)
        event_ids.append(
            self.bus.publish(
                memory_candidate_event(
                    source=self.source,
                    candidate=candidate,
                    timestamp=transcript.captured_ts,
                    ttl_ms=DEFAULT_PERCEPTION_TTL_MS,
                    event_id=f"evt_{candidate.candidate_id}",
                )
            ).event_id
        )
        self._stats["memory_candidates"] += 1
        return event_ids


class PerceptionFusionCalibrator:
    """Publishes simple cross-sensor match diagnostics for live perception."""

    def __init__(
        self,
        *,
        bus: EventBus | None = None,
        source: str = "perception_fusion",
        match_window_ms: int = 3_000,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.source = _required_text(source, "source")
        self.match_window_ms = _positive_int(match_window_ms, "match_window_ms")
        self._clock = clock or _now_ms
        self._bus: EventBus | None = None
        self._subscription: Subscription | None = None
        self._last_persons: dict[str, dict[str, Any]] = {}
        self._last_speech: dict[str, Any] | None = None
        self._stats = {"matches": 0, "speech_events": 0, "person_events": 0}
        if bus is not None:
            self.attach_to_bus(bus)

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._bus = bus
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[RuntimeEventKind.PERCEPTION_OBSERVATION],
            subscription_id=f"{self.source}_events",
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> None:
        observation_type = str(event.payload.get("observation_type", event.payload.get("type", "")))
        if observation_type == "person_seen":
            self._apply_person(event)
        elif observation_type == "speech_transcript":
            self._apply_speech(event)

    def _apply_person(self, event: RuntimeEvent) -> None:
        person_id = event.payload.get("person_id")
        if not isinstance(person_id, str) or not person_id:
            return
        self._last_persons[person_id] = {
            "person_id": person_id,
            "label": event.payload.get("label", person_id),
            "timestamp": event.timestamp,
            "confidence": event.confidence if event.confidence is not None else 0.5,
            "source": event.source,
        }
        self._stats["person_events"] += 1

    def _apply_speech(self, event: RuntimeEvent) -> None:
        speaker = event.payload.get("speaker")
        if not isinstance(speaker, str) or not speaker:
            return
        self._last_speech = {
            "speaker": speaker,
            "timestamp": event.timestamp,
            "confidence": event.confidence if event.confidence is not None else 0.5,
            "source": event.source,
        }
        self._stats["speech_events"] += 1
        match = self._match_person(speaker, event.timestamp)
        if match is not None:
            self._publish_match(event, match)

    def _match_person(self, speaker: str, timestamp: int) -> dict[str, Any] | None:
        candidates = [
            person
            for person in self._last_persons.values()
            if timestamp - int(person["timestamp"]) <= self.match_window_ms
        ]
        if not candidates:
            return None
        exact = [person for person in candidates if person["person_id"] == speaker or person["label"] == speaker]
        return (exact or sorted(candidates, key=lambda item: timestamp - int(item["timestamp"])))[0]

    def _publish_match(self, event: RuntimeEvent, person: Mapping[str, Any]) -> None:
        if self._bus is None:
            return
        latency_ms = event.timestamp - int(person["timestamp"])
        payload = {
            "value": {
                "speaker": event.payload.get("speaker"),
                "matched_person_id": person["person_id"],
                "matched_label": person["label"],
                "latency_ms": latency_ms,
                "speech_confidence": event.confidence,
                "person_confidence": person["confidence"],
            },
            "state_key": "perception_fusion",
        }
        self._bus.publish(
            world_state_update(
                source=self.source,
                state_key="perception_fusion",
                payload=payload,
                confidence=min(
                    event.confidence if event.confidence is not None else 0.5,
                    float(person["confidence"]),
                ),
                timestamp=event.timestamp,
            )
        )
        self._stats["matches"] += 1


def _first_available(
    discovery: PeripheralDiscoveryService,
    kind: PeripheralKind,
    now: int,
    *,
    preferred_device_id: str | None = None,
) -> PeripheralDevice | None:
    snapshot = discovery.last_snapshot
    if snapshot is None:
        snapshot = discovery.scan_now(now_ms=now)
    devices = snapshot.available(kind)
    if preferred_device_id:
        for device in devices:
            if device.device_id == preferred_device_id:
                return device
    return devices[0] if devices else None


def _vision_candidate(frame: CapturedFrame, trace_id: str | None) -> MemoryCandidate:
    labels = [str(item.get("label", item.get("person_id", "person"))) for item in frame.detections]
    summary = f"Camera observed {', '.join(labels)}" if labels else "Camera frame captured"
    return MemoryCandidate(
        candidate_id=f"cand_{frame.frame_id}",
        candidate_type="live_camera_observation",
        summary=summary,
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=frame.confidence,
        features=SalienceFeatures(novelty=0.7, social_relevance=0.8, task_relevance=0.5),
        entities=labels,
        tags=["live_perception", "vision", "camera_frame"],
        payload={"frame": frame.to_dict()},
        provenance_refs=[trace_id] if trace_id else [],
    )


def _speech_candidate(
    transcript: SpeechTranscriptObservation,
    trace_id: str | None,
) -> MemoryCandidate:
    explicit = 1.0 if _is_memory_instruction(transcript.transcript) else 0.0
    statement = _statement_from_memory_text(transcript.transcript)
    payload: dict[str, Any] = {
        "speaker": transcript.speaker,
        "transcript": transcript.transcript,
        "utterance": transcript.transcript,
        "topic": _topic_for_text(transcript.transcript),
        "live_transcript": transcript.to_dict(),
    }
    tags = ["live_perception", "speech", "transcript"]
    if statement is not None:
        payload["statements"] = [statement]
        tags.append("preference")
    return MemoryCandidate(
        candidate_id=f"cand_{transcript.transcript_id}",
        candidate_type="live_speech_transcript",
        summary=f"{transcript.speaker} said: {_short_text(transcript.transcript)}",
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=transcript.confidence,
        features=SalienceFeatures(
            novelty=0.8,
            task_relevance=0.8,
            social_relevance=0.8,
            surprise=0.5,
            explicit_remember_flag=explicit,
        ),
        entities=[transcript.speaker],
        tags=tags,
        payload=payload,
        provenance_refs=[trace_id] if trace_id else [],
    )


def _frame_from_file(
    *,
    frame_id: str,
    timestamp: int,
    device: PeripheralDevice,
    path: Path,
    mime_type: str,
    confidence: float,
    detections: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> CapturedFrame:
    data = path.read_bytes()
    return CapturedFrame(
        frame_id=frame_id,
        captured_ts=timestamp,
        device_id=device.device_id,
        device_label=device.label,
        path=path,
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        confidence=confidence,
        detections=detections,
        metadata=metadata,
    )


def _run_command(command: Sequence[str], timeout_ms: int) -> str:
    completed = subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_ms / 1000,
    )
    return completed.stdout


def _parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _format_command_part(part: str, values: Mapping[str, str]) -> str:
    formatted = part
    for key, value in values.items():
        formatted = formatted.replace(f"{{{key}}}", value)
    return formatted


def _topic_for_text(text: str) -> str:
    lowered = text.lower()
    if "remember" in lowered:
        return "memory_instruction"
    if "?" in text:
        return "question"
    return "conversation"


def _is_memory_instruction(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered.startswith(("remember ", "remember that ", "mneme, remember")) or " remember that " in lowered


def _statement_from_memory_text(text: str) -> dict[str, Any] | None:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    for prefix in ("mneme, remember that ", "remember that ", "remember "):
        if lowered.startswith(prefix):
            return _parse_user_statement(normalized[len(prefix) :])
    marker = " remember that "
    if marker in lowered:
        start = lowered.index(marker) + len(marker)
        return _parse_user_statement(normalized[start:])
    return None


def _parse_user_statement(statement: str) -> dict[str, Any] | None:
    lowered = statement.strip().lower()
    if lowered.startswith("i like "):
        return {
            "subject": "user",
            "predicate": "likes",
            "value": statement.strip()[len("i like ") :].strip(),
            "confidence": 0.9,
        }
    return None


def _short_text(text: str, limit: int = 120) -> str:
    normalized = " ".join(text.split())
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 1]}..."


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)


def _unlink(path: Path) -> None:
    try:
        path.unlink()
        sidecar = path.with_suffix(f"{path.suffix}.json")
        if sidecar.exists():
            sidecar.unlink()
    except FileNotFoundError:
        return


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of mappings")
    items = list(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError(f"{field_name} must be a list of mappings")
    return [dict(item) for item in items]


def _string_list(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must be a list of strings")
    return items


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
