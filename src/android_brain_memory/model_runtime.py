from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5b"
DEFAULT_MODEL_TIMEOUT_MS = 5_000

MODEL_ROLES = {"system", "user", "assistant"}


@dataclass(slots=True)
class ModelMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        self.role = _required_text(self.role, "role")
        if self.role not in MODEL_ROLES:
            raise ValueError(f"role must be one of {sorted(MODEL_ROLES)}")
        self.content = _required_text(self.content, "content")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ModelMessage":
        return cls(role=data.get("role"), content=data.get("content"))

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}


@dataclass(slots=True)
class ModelRequest:
    model: str
    messages: list[ModelMessage]
    options: dict[str, Any] = field(default_factory=dict)
    response_format: str | dict[str, Any] | None = None
    timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS

    def __post_init__(self) -> None:
        self.model = _required_text(self.model, "model")
        self.messages = [
            message if isinstance(message, ModelMessage) else ModelMessage.from_dict(message)
            for message in self.messages
        ]
        if not self.messages:
            raise ValueError("messages must not be empty")
        if not isinstance(self.options, dict):
            raise ValueError("options must be a dictionary")
        if self.response_format is not None and not isinstance(self.response_format, (str, dict)):
            raise ValueError("response_format must be a string, dictionary, or None")
        if isinstance(self.response_format, str):
            self.response_format = _required_text(self.response_format, "response_format")
        if isinstance(self.response_format, dict):
            self.response_format = dict(self.response_format)
        self.timeout_ms = _positive_int(self.timeout_ms, "timeout_ms")

    @classmethod
    def from_prompt(
        cls,
        text: str,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        system: str | None = None,
        timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS,
        options: Mapping[str, Any] | None = None,
        response_format: str | dict[str, Any] | None = None,
    ) -> "ModelRequest":
        messages = []
        if system:
            messages.append(ModelMessage(role="system", content=system))
        messages.append(ModelMessage(role="user", content=text))
        return cls(
            model=model,
            messages=messages,
            options=dict(options or {}),
            response_format=response_format,
            timeout_ms=timeout_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "options": dict(self.options),
            "response_format": self.response_format,
            "timeout_ms": self.timeout_ms,
        }


@dataclass(slots=True)
class ModelResponse:
    ok: bool
    backend: str
    model: str
    text: str = ""
    error_code: str | None = None
    error: str | None = None
    latency_ms: int | None = None
    total_duration_ns: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "backend": self.backend,
            "model": self.model,
            "text": self.text,
            "error_code": self.error_code,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "total_duration_ns": self.total_duration_ns,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ModelListResult:
    ok: bool
    backend: str
    models: list[dict[str, Any]] = field(default_factory=list)
    error_code: str | None = None
    error: str | None = None
    latency_ms: int | None = None

    @property
    def model_names(self) -> list[str]:
        names: set[str] = set()
        for item in self.models:
            name = item.get("name")
            model = item.get("model")
            if isinstance(name, str) and name:
                names.add(name)
            if isinstance(model, str) and model:
                names.add(model)
        return sorted(names)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "backend": self.backend,
            "models": list(self.models),
            "model_names": self.model_names,
            "error_code": self.error_code,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


@dataclass(slots=True)
class ModelRuntimeCheck:
    ok: bool
    backend: str
    model: str
    server_available: bool
    model_available: bool
    available_models: list[str] = field(default_factory=list)
    probe_ran: bool = False
    probe_response: ModelResponse | None = None
    error_code: str | None = None
    error: str | None = None
    suggestion: str | None = None
    latency_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "backend": self.backend,
            "model": self.model,
            "server_available": self.server_available,
            "model_available": self.model_available,
            "available_models": list(self.available_models),
            "probe_ran": self.probe_ran,
            "probe_response": self.probe_response.to_dict() if self.probe_response else None,
            "error_code": self.error_code,
            "error": self.error,
            "suggestion": self.suggestion,
            "latency_ms": self.latency_ms,
        }


class ModelRuntimeAdapter(Protocol):
    backend: str

    def list_models(self, *, timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS) -> ModelListResult:
        ...

    def generate(self, request: ModelRequest) -> ModelResponse:
        ...

    def check_model(
        self,
        model: str,
        *,
        probe: bool = True,
        timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS,
    ) -> ModelRuntimeCheck:
        ...


class ModelRuntimeRequestError(Exception):
    def __init__(self, error_code: str, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code


HttpJsonClient = Callable[[str, str, Mapping[str, Any] | None, float], tuple[int, Mapping[str, Any]]]


class FakeModelRuntime:
    backend = "fake"

    def __init__(
        self,
        *,
        available_models: Sequence[str] = (DEFAULT_OLLAMA_MODEL,),
        response_text: str = "ready",
        failure_code: str | None = None,
        failure_message: str | None = None,
        latency_ms: int = 1,
    ) -> None:
        self.available_models = list(available_models)
        self.response_text = response_text
        self.failure_code = failure_code
        self.failure_message = failure_message
        self.latency_ms = latency_ms

    def list_models(self, *, timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS) -> ModelListResult:
        if self.failure_code == "server_unavailable":
            return ModelListResult(
                ok=False,
                backend=self.backend,
                error_code=self.failure_code,
                error=self.failure_message or "fake runtime unavailable",
                latency_ms=self.latency_ms,
            )
        return ModelListResult(
            ok=True,
            backend=self.backend,
            models=[{"name": model, "model": model} for model in self.available_models],
            latency_ms=self.latency_ms,
        )

    def generate(self, request: ModelRequest) -> ModelResponse:
        if self.failure_code and self.failure_code != "server_unavailable":
            return ModelResponse(
                ok=False,
                backend=self.backend,
                model=request.model,
                error_code=self.failure_code,
                error=self.failure_message or "fake runtime failure",
                latency_ms=self.latency_ms,
            )
        if request.model not in self.available_models:
            return ModelResponse(
                ok=False,
                backend=self.backend,
                model=request.model,
                error_code="model_missing",
                error=f"model is not installed: {request.model}",
                latency_ms=self.latency_ms,
            )
        return ModelResponse(
            ok=True,
            backend=self.backend,
            model=request.model,
            text=self.response_text,
            latency_ms=self.latency_ms,
        )

    def check_model(
        self,
        model: str,
        *,
        probe: bool = True,
        timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS,
    ) -> ModelRuntimeCheck:
        return check_model_runtime(self, model, probe=probe, timeout_ms=timeout_ms)


class OllamaModelRuntime:
    backend = "ollama"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        http_json: HttpJsonClient | None = None,
    ) -> None:
        self.base_url = _required_text(base_url, "base_url").rstrip("/")
        self._http_json = http_json or _urllib_http_json

    def list_models(self, *, timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS) -> ModelListResult:
        started = time.monotonic()
        try:
            _, payload = self._http_json("GET", f"{self.base_url}/api/tags", None, timeout_ms / 1000)
            raw_models = payload.get("models", [])
            if not isinstance(raw_models, list):
                return ModelListResult(
                    ok=False,
                    backend=self.backend,
                    error_code="malformed_response",
                    error="/api/tags response did not contain a models list",
                    latency_ms=_elapsed_ms(started),
                )
            models = [dict(item) for item in raw_models if isinstance(item, Mapping)]
            return ModelListResult(
                ok=True,
                backend=self.backend,
                models=models,
                latency_ms=_elapsed_ms(started),
            )
        except ModelRuntimeRequestError as exc:
            return ModelListResult(
                ok=False,
                backend=self.backend,
                error_code=exc.error_code,
                error=str(exc),
                latency_ms=_elapsed_ms(started),
            )

    def generate(self, request: ModelRequest) -> ModelResponse:
        started = time.monotonic()
        try:
            payload: dict[str, Any] = {
                "model": request.model,
                "messages": [message.to_dict() for message in request.messages],
                "stream": False,
            }
            if request.options:
                payload["options"] = dict(request.options)
            if request.response_format is not None:
                payload["format"] = request.response_format
            _, response = self._http_json(
                "POST",
                f"{self.base_url}/api/chat",
                payload,
                request.timeout_ms / 1000,
            )
            message = response.get("message", {})
            text = ""
            if isinstance(message, Mapping):
                content = message.get("content")
                if isinstance(content, str):
                    text = content
            if not text and isinstance(response.get("response"), str):
                text = str(response["response"])
            if not isinstance(text, str):
                text = ""
            if not text.strip():
                return ModelResponse(
                    ok=False,
                    backend=self.backend,
                    model=request.model,
                    error_code="malformed_response",
                    error="/api/chat response did not contain assistant text",
                    latency_ms=_elapsed_ms(started),
                    metadata=_response_metadata(response),
                )
            return ModelResponse(
                ok=True,
                backend=self.backend,
                model=str(response.get("model") or request.model),
                text=text.strip(),
                latency_ms=_elapsed_ms(started),
                total_duration_ns=_optional_int(response.get("total_duration")),
                metadata=_response_metadata(response),
            )
        except ModelRuntimeRequestError as exc:
            return ModelResponse(
                ok=False,
                backend=self.backend,
                model=request.model,
                error_code=exc.error_code,
                error=str(exc),
                latency_ms=_elapsed_ms(started),
            )

    def check_model(
        self,
        model: str,
        *,
        probe: bool = True,
        timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS,
    ) -> ModelRuntimeCheck:
        return check_model_runtime(self, model, probe=probe, timeout_ms=timeout_ms)


def check_model_runtime(
    adapter: ModelRuntimeAdapter,
    model: str,
    *,
    probe: bool = True,
    timeout_ms: int = DEFAULT_MODEL_TIMEOUT_MS,
) -> ModelRuntimeCheck:
    clean_model = _required_text(model, "model")
    started = time.monotonic()
    model_list = adapter.list_models(timeout_ms=timeout_ms)
    if not model_list.ok:
        return ModelRuntimeCheck(
            ok=False,
            backend=adapter.backend,
            model=clean_model,
            server_available=False,
            model_available=False,
            error_code=model_list.error_code or "server_unavailable",
            error=model_list.error,
            suggestion=_suggestion(adapter.backend, clean_model, model_list.error_code),
            latency_ms=_elapsed_ms(started),
        )
    available = model_list.model_names
    if clean_model not in available:
        return ModelRuntimeCheck(
            ok=False,
            backend=adapter.backend,
            model=clean_model,
            server_available=True,
            model_available=False,
            available_models=available,
            error_code="model_missing",
            error=f"model is not installed: {clean_model}",
            suggestion=_suggestion(adapter.backend, clean_model, "model_missing"),
            latency_ms=_elapsed_ms(started),
        )
    if not probe:
        return ModelRuntimeCheck(
            ok=True,
            backend=adapter.backend,
            model=clean_model,
            server_available=True,
            model_available=True,
            available_models=available,
            probe_ran=False,
            latency_ms=_elapsed_ms(started),
        )
    request = ModelRequest.from_prompt(
        "Reply with the single word: ready",
        model=clean_model,
        system="You are Mneme's local cognition health check. Keep the answer minimal.",
        timeout_ms=timeout_ms,
        options={"temperature": 0, "num_predict": 16},
    )
    response = adapter.generate(request)
    if not response.ok:
        return ModelRuntimeCheck(
            ok=False,
            backend=adapter.backend,
            model=clean_model,
            server_available=True,
            model_available=True,
            available_models=available,
            probe_ran=True,
            probe_response=response,
            error_code=response.error_code,
            error=response.error,
            suggestion=_suggestion(adapter.backend, clean_model, response.error_code),
            latency_ms=_elapsed_ms(started),
        )
    return ModelRuntimeCheck(
        ok=True,
        backend=adapter.backend,
        model=clean_model,
        server_available=True,
        model_available=True,
        available_models=available,
        probe_ran=True,
        probe_response=response,
        latency_ms=_elapsed_ms(started),
    )


def _urllib_http_json(
    method: str,
    url: str,
    payload: Mapping[str, Any] | None,
    timeout_s: float,
) -> tuple[int, Mapping[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
            status = response.getcode()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = _error_message(body) or f"Ollama returned HTTP {exc.code}"
        raise ModelRuntimeRequestError("http_error", message, status_code=exc.code) from exc
    except TimeoutError as exc:
        raise ModelRuntimeRequestError("timeout", "Ollama request timed out") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise ModelRuntimeRequestError("server_unavailable", f"Ollama is unavailable: {reason}") from exc
    except OSError as exc:
        raise ModelRuntimeRequestError("server_unavailable", f"Ollama is unavailable: {exc}") from exc
    if not raw.strip():
        return status, {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelRuntimeRequestError("malformed_response", "Ollama returned invalid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ModelRuntimeRequestError("malformed_response", "Ollama returned non-object JSON")
    return status, parsed


def _error_message(body: str) -> str | None:
    if not body.strip():
        return None
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()
    if isinstance(parsed, Mapping):
        error = parsed.get("error")
        if isinstance(error, str) and error.strip():
            return error.strip()
    return None


def _response_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    keys = [
        "created_at",
        "done",
        "done_reason",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    ]
    return {key: payload[key] for key in keys if key in payload}


def _suggestion(backend: str, model: str, error_code: str | None) -> str | None:
    if backend == "ollama" and error_code == "model_missing":
        return f"Run: ollama pull {model}"
    if backend == "ollama" and error_code == "server_unavailable":
        return "Start Ollama, then retry the cognition check."
    return None


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.monotonic() - started) * 1000))


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
