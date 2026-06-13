from __future__ import annotations

import json

from android_brain_memory.model_runtime import (
    DEFAULT_OLLAMA_MODEL,
    FakeModelRuntime,
    ModelRequest,
    ModelRuntimeCheck,
    ModelRuntimeRequestError,
    OllamaModelRuntime,
)
from android_brain_memory.virtual_head import main as mneme_main


def test_fake_model_runtime_check_reports_available_model():
    runtime = FakeModelRuntime(available_models=[DEFAULT_OLLAMA_MODEL], response_text="ready")

    result = runtime.check_model(DEFAULT_OLLAMA_MODEL)

    assert result.ok is True
    assert result.server_available is True
    assert result.model_available is True
    assert result.probe_ran is True
    assert result.probe_response is not None
    assert result.probe_response.text == "ready"


def test_ollama_list_models_parses_name_and_model_fields():
    def fake_http(method, url, payload, timeout_s):
        assert method == "GET"
        assert url == "http://localhost:11434/api/tags"
        assert payload is None
        return 200, {
            "models": [
                {"name": "qwen2.5:1.5b", "model": "qwen2.5:1.5b"},
                {"name": "phi3.5", "details": {"parameter_size": "3.8B"}},
            ]
        }

    result = OllamaModelRuntime(http_json=fake_http).list_models()

    assert result.ok is True
    assert result.model_names == ["phi3.5", "qwen2.5:1.5b"]


def test_ollama_chat_sends_non_streaming_request_and_parses_response():
    seen = {}

    def fake_http(method, url, payload, timeout_s):
        seen["method"] = method
        seen["url"] = url
        seen["payload"] = payload
        return 200, {
            "model": "qwen2.5:1.5b",
            "message": {"role": "assistant", "content": "ready"},
            "done": True,
            "done_reason": "stop",
            "total_duration": 123,
            "eval_count": 1,
        }

    runtime = OllamaModelRuntime(http_json=fake_http)
    response = runtime.generate(ModelRequest.from_prompt("health?", model=DEFAULT_OLLAMA_MODEL))

    assert response.ok is True
    assert response.text == "ready"
    assert response.total_duration_ns == 123
    assert seen["method"] == "POST"
    assert seen["url"] == "http://localhost:11434/api/chat"
    assert seen["payload"]["stream"] is False
    assert seen["payload"]["model"] == DEFAULT_OLLAMA_MODEL


def test_ollama_check_reports_missing_model_with_pull_suggestion():
    def fake_http(method, url, payload, timeout_s):
        return 200, {"models": [{"name": "phi3.5"}]}

    result = OllamaModelRuntime(http_json=fake_http).check_model(DEFAULT_OLLAMA_MODEL)

    assert result.ok is False
    assert result.server_available is True
    assert result.model_available is False
    assert result.error_code == "model_missing"
    assert result.suggestion == f"Run: ollama pull {DEFAULT_OLLAMA_MODEL}"


def test_ollama_check_reports_server_unavailable():
    def fake_http(method, url, payload, timeout_s):
        raise ModelRuntimeRequestError("server_unavailable", "Ollama is unavailable")

    result = OllamaModelRuntime(http_json=fake_http).check_model(DEFAULT_OLLAMA_MODEL)

    assert result.ok is False
    assert result.server_available is False
    assert result.error_code == "server_unavailable"
    assert result.suggestion == "Start Ollama, then retry the cognition check."


def test_ollama_check_reports_timeout():
    def fake_http(method, url, payload, timeout_s):
        raise ModelRuntimeRequestError("timeout", "Ollama request timed out")

    result = OllamaModelRuntime(http_json=fake_http).check_model(DEFAULT_OLLAMA_MODEL)

    assert result.ok is False
    assert result.server_available is False
    assert result.error_code == "timeout"
    assert result.error == "Ollama request timed out"


def test_ollama_check_reports_malformed_tags_response():
    def fake_http(method, url, payload, timeout_s):
        return 200, {"models": "not-a-list"}

    result = OllamaModelRuntime(http_json=fake_http).check_model(DEFAULT_OLLAMA_MODEL)

    assert result.ok is False
    assert result.server_available is False
    assert result.error_code == "malformed_response"


def test_ollama_generate_reports_empty_or_malformed_chat_response():
    def fake_http(method, url, payload, timeout_s):
        return 200, {"model": DEFAULT_OLLAMA_MODEL, "message": {"role": "assistant"}}

    response = OllamaModelRuntime(http_json=fake_http).generate(
        ModelRequest.from_prompt("health?", model=DEFAULT_OLLAMA_MODEL)
    )

    assert response.ok is False
    assert response.error_code == "malformed_response"


def test_cognition_check_json_cli_success_uses_structured_output(monkeypatch, capsys):
    class FakeOllama:
        def __init__(self, *, base_url: str) -> None:
            self.base_url = base_url

        def check_model(self, model: str, *, probe: bool, timeout_ms: int) -> ModelRuntimeCheck:
            return ModelRuntimeCheck(
                ok=True,
                backend="ollama",
                model=model,
                server_available=True,
                model_available=True,
                available_models=[model],
                probe_ran=probe,
                latency_ms=3,
            )

    monkeypatch.setattr("android_brain_memory.virtual_head.OllamaModelRuntime", FakeOllama)

    code = mneme_main(["cognition", "check", "--json", "--no-probe"])
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["ok"] is True
    assert output["backend"] == "ollama"
    assert output["model"] == DEFAULT_OLLAMA_MODEL
    assert output["probe_ran"] is False


def test_cognition_check_json_cli_failure_returns_nonzero(monkeypatch, capsys):
    class FakeOllama:
        def __init__(self, *, base_url: str) -> None:
            self.base_url = base_url

        def check_model(self, model: str, *, probe: bool, timeout_ms: int) -> ModelRuntimeCheck:
            return ModelRuntimeCheck(
                ok=False,
                backend="ollama",
                model=model,
                server_available=True,
                model_available=False,
                error_code="model_missing",
                error=f"model is not installed: {model}",
                suggestion=f"Run: ollama pull {model}",
            )

    monkeypatch.setattr("android_brain_memory.virtual_head.OllamaModelRuntime", FakeOllama)

    code = mneme_main(["cognition", "check", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert code == 1
    assert output["ok"] is False
    assert output["error_code"] == "model_missing"
    assert output["suggestion"] == f"Run: ollama pull {DEFAULT_OLLAMA_MODEL}"
