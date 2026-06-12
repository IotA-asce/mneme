from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .live_perception import CameraCaptureBackend, CapturedFrame
from .models import validate_confidence, validate_timestamp
from .peripherals import PeripheralDevice


class FaceDetectionBackend:
    def detect(self, image_path: Path) -> list[dict[str, Any]]:
        raise NotImplementedError


class MediaPipeFaceDetectionBackend(FaceDetectionBackend):
    """Optional MediaPipe face detector for local person presence."""

    def __init__(
        self,
        *,
        min_detection_confidence: float = 0.5,
        model_selection: int = 0,
        mediapipe_module: Any | None = None,
        cv2_module: Any | None = None,
    ) -> None:
        self.min_detection_confidence = validate_confidence(min_detection_confidence)
        if model_selection not in {0, 1}:
            raise ValueError("model_selection must be 0 or 1")
        self.model_selection = model_selection
        self._mediapipe = mediapipe_module
        self._cv2 = cv2_module

    def detect(self, image_path: Path) -> list[dict[str, Any]]:
        mp = self._mediapipe or _import_optional("mediapipe", "vision-local")
        cv2 = self._cv2 or _import_optional("cv2", "vision-local")
        image = cv2.imread(str(image_path))
        if image is None:
            return []
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        detections: list[dict[str, Any]] = []
        face_detection = mp.solutions.face_detection
        with face_detection.FaceDetection(
            model_selection=self.model_selection,
            min_detection_confidence=self.min_detection_confidence,
        ) as detector:
            results = detector.process(rgb)
        for index, detection in enumerate(getattr(results, "detections", []) or []):
            detections.append(_mediapipe_detection_to_dict(detection, index))
        return detections


class OpenCVCameraCaptureBackend(CameraCaptureBackend):
    """Captures one frame from a local camera through optional OpenCV."""

    def __init__(
        self,
        *,
        camera_index: int | None = None,
        cv2_module: Any | None = None,
        face_detector: FaceDetectionBackend | Callable[[Path], list[dict[str, Any]]] | None = None,
        mime_type: str = "image/jpeg",
    ) -> None:
        self.camera_index = camera_index
        self._cv2 = cv2_module
        self.face_detector = face_detector
        self.mime_type = _required_text(mime_type, "mime_type")

    def capture(
        self,
        *,
        device: PeripheralDevice,
        output_path: Path,
        timestamp: int,
    ) -> CapturedFrame | None:
        ts = validate_timestamp(timestamp, "timestamp")
        cv2 = self._cv2 or _import_optional("cv2", "vision-local")
        camera_ref = self.camera_index
        if camera_ref is None:
            metadata_index = device.metadata.get("index") if isinstance(device.metadata, Mapping) else None
            camera_ref = metadata_index if isinstance(metadata_index, int) else 0
        capture = cv2.VideoCapture(camera_ref)
        try:
            if hasattr(capture, "isOpened") and not capture.isOpened():
                return None
            ok, frame = capture.read()
            if not ok:
                return None
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(output_path), frame):
                return None
        finally:
            if hasattr(capture, "release"):
                capture.release()
        detections = self._detect_faces(output_path)
        data = output_path.read_bytes()
        import hashlib

        return CapturedFrame(
            frame_id=f"frame_{uuid.uuid4().hex[:12]}",
            captured_ts=ts,
            device_id=device.device_id,
            device_label=device.label,
            path=output_path,
            mime_type=self.mime_type,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            confidence=0.82,
            detections=detections,
            metadata={
                "backend": "opencv",
                "camera_ref": camera_ref,
                "face_detector": type(self.face_detector).__name__ if self.face_detector else None,
            },
        )

    def _detect_faces(self, output_path: Path) -> list[dict[str, Any]]:
        detector = self.face_detector
        if detector is None:
            return []
        if isinstance(detector, FaceDetectionBackend):
            return detector.detect(output_path)
        return _mapping_list(detector(output_path), "detections")


def _mediapipe_detection_to_dict(detection: Any, index: int) -> dict[str, Any]:
    score = 0.5
    raw_scores = getattr(detection, "score", None)
    if isinstance(raw_scores, Sequence) and raw_scores:
        score = float(raw_scores[0])
    bbox = {}
    location = getattr(detection, "location_data", None)
    relative_bbox = getattr(location, "relative_bounding_box", None)
    if relative_bbox is not None:
        bbox = {
            "xmin": float(getattr(relative_bbox, "xmin", 0.0)),
            "ymin": float(getattr(relative_bbox, "ymin", 0.0)),
            "width": float(getattr(relative_bbox, "width", 0.0)),
            "height": float(getattr(relative_bbox, "height", 0.0)),
        }
    keypoints = []
    for keypoint in getattr(location, "relative_keypoints", []) or []:
        keypoints.append({
            "x": float(getattr(keypoint, "x", 0.0)),
            "y": float(getattr(keypoint, "y", 0.0)),
        })
    return {
        "person_id": f"session_person_{index + 1}",
        "label": f"person_{index + 1}",
        "confidence": validate_confidence(score),
        "bbox": bbox,
        "keypoints": keypoints,
        "attention_facing_signal": bool(keypoints),
        "identity_status": "anonymous_session",
        "source": "mediapipe_face_detection",
    }


def _import_optional(module_name: str, extra_name: str) -> Any:
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise ValueError(
            f"optional dependency '{module_name}' is required; install android-brain-memory[{extra_name}]"
        ) from exc


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if isinstance(value, Mapping) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of mappings")
    items = list(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError(f"{field_name} must be a list of mappings")
    return [dict(item) for item in items]
