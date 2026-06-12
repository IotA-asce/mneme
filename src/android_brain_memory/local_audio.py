from __future__ import annotations

import time
import wave
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .live_perception import SpeechRecognitionBackend, SpeechTranscriptObservation
from .peripherals import PeripheralDevice
from .presence import SpeechOutput, SpeechOutputBackend
from .models import validate_confidence, validate_timestamp


DEFAULT_AUDIO_DIR = Path(".local/audio_segments")
DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH_BYTES = 2


@dataclass(slots=True)
class AudioCapture:
    capture_id: str
    captured_ts: int
    path: Path | str
    sample_rate: int = DEFAULT_SAMPLE_RATE
    channels: int = DEFAULT_CHANNELS
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.capture_id = _required_text(self.capture_id, "capture_id")
        self.captured_ts = validate_timestamp(self.captured_ts, "captured_ts")
        self.path = Path(self.path)
        self.sample_rate = _positive_int(self.sample_rate, "sample_rate")
        self.channels = _positive_int(self.channels, "channels")
        self.duration_ms = _non_negative_int(self.duration_ms, "duration_ms")
        self.metadata = _json_mapping(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "capture_id": self.capture_id,
            "captured_ts": self.captured_ts,
            "path": str(self.path),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
        }


class SoundDeviceMicrophoneRecorder:
    """Records a bounded microphone segment to WAV using optional sounddevice."""

    def __init__(
        self,
        *,
        audio_dir: str | Path = DEFAULT_AUDIO_DIR,
        duration_ms: int = 3_000,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
        sounddevice_module: Any | None = None,
        numpy_module: Any | None = None,
    ) -> None:
        self.audio_dir = Path(audio_dir)
        self.duration_ms = _positive_int(duration_ms, "duration_ms")
        self.sample_rate = _positive_int(sample_rate, "sample_rate")
        self.channels = _positive_int(channels, "channels")
        self._sounddevice = sounddevice_module
        self._numpy = numpy_module

    def record(self, *, device: PeripheralDevice, timestamp: int) -> AudioCapture:
        ts = validate_timestamp(timestamp, "timestamp")
        sd = self._sounddevice or _import_optional("sounddevice", "audio-local")
        np = self._numpy or _import_optional("numpy", "audio-local")
        frames = max(1, int(self.sample_rate * self.duration_ms / 1000))
        try:
            data = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                device=_sounddevice_device(device),
                blocking=True,
            )
            if hasattr(sd, "wait"):
                sd.wait()
        except Exception as exc:  # pragma: no cover - real backend only
            raise ValueError(f"microphone capture failed: {type(exc).__name__}") from exc
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        path = self.audio_dir / f"{ts}_mic.wav"
        array = np.asarray(data, dtype=np.int16)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(DEFAULT_SAMPLE_WIDTH_BYTES)
            wav.setframerate(self.sample_rate)
            wav.writeframes(array.tobytes())
        return AudioCapture(
            capture_id=f"audio_{ts}",
            captured_ts=ts,
            path=path,
            sample_rate=self.sample_rate,
            channels=self.channels,
            duration_ms=self.duration_ms,
            metadata={"backend": "sounddevice", "device_id": device.device_id},
        )


@dataclass(slots=True)
class VadDecision:
    speech_frames: int
    total_frames: int
    speech_ratio: float
    is_speech: bool

    def __post_init__(self) -> None:
        self.speech_frames = _non_negative_int(self.speech_frames, "speech_frames")
        self.total_frames = _positive_int(self.total_frames, "total_frames")
        self.speech_ratio = validate_confidence(self.speech_ratio)
        if not isinstance(self.is_speech, bool):
            raise ValueError("is_speech must be a boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "speech_frames": self.speech_frames,
            "total_frames": self.total_frames,
            "speech_ratio": self.speech_ratio,
            "is_speech": self.is_speech,
        }


class WebRtcVadEndpointDetector:
    """Small first-pass VAD wrapper; it never runs unless optional deps are installed."""

    def __init__(
        self,
        *,
        aggressiveness: int = 2,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        frame_ms: int = 30,
        min_speech_ratio: float = 0.35,
        vad_factory: Callable[[int], Any] | None = None,
    ) -> None:
        if aggressiveness < 0 or aggressiveness > 3:
            raise ValueError("aggressiveness must be between 0 and 3")
        self.aggressiveness = aggressiveness
        self.sample_rate = _positive_int(sample_rate, "sample_rate")
        self.frame_ms = _positive_int(frame_ms, "frame_ms")
        self.min_speech_ratio = validate_confidence(min_speech_ratio)
        self._vad_factory = vad_factory

    def classify(self, pcm16: bytes) -> VadDecision:
        if not pcm16:
            return VadDecision(0, 1, 0.0, False)
        vad = self._build_vad()
        frame_size = int(self.sample_rate * self.frame_ms / 1000) * DEFAULT_SAMPLE_WIDTH_BYTES
        frames = [
            pcm16[index : index + frame_size]
            for index in range(0, len(pcm16), frame_size)
            if len(pcm16[index : index + frame_size]) == frame_size
        ]
        if not frames:
            return VadDecision(0, 1, 0.0, False)
        speech_frames = sum(1 for frame in frames if bool(vad.is_speech(frame, self.sample_rate)))
        ratio = speech_frames / len(frames)
        return VadDecision(
            speech_frames=speech_frames,
            total_frames=len(frames),
            speech_ratio=ratio,
            is_speech=ratio >= self.min_speech_ratio,
        )

    def _build_vad(self) -> Any:
        if self._vad_factory is not None:
            return self._vad_factory(self.aggressiveness)
        try:
            webrtcvad = _import_optional("webrtcvad", "vad-local")
        except ValueError:
            webrtcvad = _import_optional("webrtcvad_wheels", "vad-local")
        return webrtcvad.Vad(self.aggressiveness)


class FasterWhisperSpeechRecognitionBackend(SpeechRecognitionBackend):
    """Records a bounded mic segment and transcribes it through faster-whisper."""

    def __init__(
        self,
        *,
        model_name_or_path: str | Path = "base",
        recorder: SoundDeviceMicrophoneRecorder | None = None,
        model_factory: Callable[..., Any] | None = None,
        language: str | None = None,
        device_name: str = "cpu",
        compute_type: str = "int8",
        beam_size: int = 5,
        default_speaker: str = "user",
    ) -> None:
        self.model_name_or_path = str(model_name_or_path)
        self.recorder = recorder or SoundDeviceMicrophoneRecorder()
        self.model_factory = model_factory
        self.language = _optional_text(language, "language")
        self.device_name = _required_text(device_name, "device_name")
        self.compute_type = _required_text(compute_type, "compute_type")
        self.beam_size = _positive_int(beam_size, "beam_size")
        self.default_speaker = _required_text(default_speaker, "default_speaker")
        self._model: Any | None = None

    def transcribe(
        self,
        *,
        device: PeripheralDevice,
        timestamp: int,
    ) -> SpeechTranscriptObservation | None:
        ts = validate_timestamp(timestamp, "timestamp")
        capture = self.recorder.record(device=device, timestamp=ts)
        model = self._get_model()
        kwargs: dict[str, Any] = {"beam_size": self.beam_size}
        if self.language:
            kwargs["language"] = self.language
        try:
            segments, info = model.transcribe(str(capture.path), **kwargs)
            segment_list = list(segments)
        except Exception as exc:  # pragma: no cover - real backend only
            raise ValueError(f"ASR transcription failed: {type(exc).__name__}") from exc
        text = " ".join(str(getattr(segment, "text", "")).strip() for segment in segment_list).strip()
        if not text:
            return None
        confidence = _confidence_from_segments(segment_list, info)
        return SpeechTranscriptObservation(
            transcript_id=f"transcript_{capture.capture_id}",
            captured_ts=ts,
            device_id=device.device_id,
            device_label=device.label,
            speaker=self.default_speaker,
            transcript=text,
            confidence=confidence,
            duration_ms=capture.duration_ms or _duration_from_info(info),
            metadata={
                "backend": "faster_whisper",
                "model": self.model_name_or_path,
                "audio": capture.to_dict(),
                "language": getattr(info, "language", None),
                "language_probability": getattr(info, "language_probability", None),
            },
        )

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self.model_factory is not None:
            self._model = self.model_factory(
                self.model_name_or_path,
                device=self.device_name,
                compute_type=self.compute_type,
            )
            return self._model
        faster_whisper = _import_optional("faster_whisper", "asr-local")
        self._model = faster_whisper.WhisperModel(
            self.model_name_or_path,
            device=self.device_name,
            compute_type=self.compute_type,
        )
        return self._model


class KokoroSpeechOutputBackend(SpeechOutputBackend):
    """Optional Kokoro-backed TTS adapter with injectable pipeline for tests."""

    def __init__(
        self,
        *,
        voice: str = "af_heart",
        language_code: str = "a",
        pipeline_factory: Callable[..., Any] | None = None,
        audio_player: Callable[[Any, int], None] | None = None,
        sample_rate: int = 24_000,
    ) -> None:
        self.voice = _required_text(voice, "voice")
        self.language_code = _required_text(language_code, "language_code")
        self.pipeline_factory = pipeline_factory
        self.audio_player = audio_player
        self.sample_rate = _positive_int(sample_rate, "sample_rate")
        self._pipeline: Any | None = None

    def speak(
        self,
        *,
        text: str,
        voice: str | None,
        device_id: str | None,
        timestamp: int,
    ) -> SpeechOutput:
        clean_text = _required_text(text, "text")
        ts = validate_timestamp(timestamp, "timestamp")
        selected_voice = _optional_text(voice, "voice") or self.voice
        pipeline = self._get_pipeline()
        try:
            chunks = list(pipeline(clean_text, voice=selected_voice))
            audio_chunks = [chunk[-1] if isinstance(chunk, tuple) else chunk for chunk in chunks]
            if self.audio_player is not None:
                for audio in audio_chunks:
                    self.audio_player(audio, self.sample_rate)
        except Exception as exc:  # pragma: no cover - real backend only
            raise ValueError(f"Kokoro TTS failed: {type(exc).__name__}") from exc
        return SpeechOutput(
            output_id=f"speech_{int(time.time() * 1000)}",
            text=clean_text,
            created_ts=ts,
            status="spoken",
            voice=selected_voice,
            device_id=device_id,
            metadata={
                "backend": "kokoro",
                "chunks": len(audio_chunks),
                "sample_rate": self.sample_rate,
            },
        )

    def _get_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        if self.pipeline_factory is not None:
            self._pipeline = self.pipeline_factory(lang_code=self.language_code)
            return self._pipeline
        kokoro = _import_optional("kokoro", "tts-local")
        pipeline_cls = getattr(kokoro, "KPipeline", None) or getattr(kokoro, "Pipeline", None)
        if pipeline_cls is None:
            raise ValueError("kokoro package does not expose KPipeline/Pipeline")
        self._pipeline = pipeline_cls(lang_code=self.language_code)
        return self._pipeline


def write_silent_wav(
    path: str | Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    duration_ms: int = 300,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frames = int(sample_rate * duration_ms / 1000)
    with wave.open(str(target), "wb") as wav:
        wav.setnchannels(DEFAULT_CHANNELS)
        wav.setsampwidth(DEFAULT_SAMPLE_WIDTH_BYTES)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)
    return target


def pcm16_frames(samples: Iterable[int]) -> bytes:
    data = bytearray()
    for sample in samples:
        value = max(-32768, min(32767, int(sample)))
        data.extend(value.to_bytes(2, byteorder="little", signed=True))
    return bytes(data)


def _confidence_from_segments(segments: Sequence[Any], info: Any) -> float:
    if not segments:
        return validate_confidence(getattr(info, "language_probability", 0.5) or 0.5)
    no_speech_values = [
        float(getattr(segment, "no_speech_prob"))
        for segment in segments
        if getattr(segment, "no_speech_prob", None) is not None
    ]
    if no_speech_values:
        return validate_confidence(1.0 - min(max(sum(no_speech_values) / len(no_speech_values), 0.0), 1.0))
    return validate_confidence(getattr(info, "language_probability", 0.8) or 0.8)


def _duration_from_info(info: Any) -> int | None:
    duration = getattr(info, "duration", None)
    if duration is None:
        return None
    return max(1, int(float(duration) * 1000))


def _sounddevice_device(device: PeripheralDevice) -> str | int | None:
    raw = device.metadata.get("index") if isinstance(device.metadata, Mapping) else None
    if isinstance(raw, int):
        return raw
    return None


def _import_optional(module_name: str, extra_name: str) -> Any:
    try:
        module = __import__(module_name)
    except ImportError as exc:
        raise ValueError(
            f"optional dependency '{module_name}' is required; install android-brain-memory[{extra_name}]"
        ) from exc
    return module


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


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)
