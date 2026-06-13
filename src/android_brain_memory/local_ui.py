from __future__ import annotations

import html
import json
from string import Template
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs

from .engine import to_jsonable
from .runtime_loop import MnemeRuntime


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mneme Local Living Lab</title>
  <style>
    :root {
      color-scheme: light;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f4ef;
      color: #161616;
      --ink: #161616;
      --muted: #6f6a60;
      --line: #d9d3c8;
      --paper: #fffdf8;
      --field: #f1ede4;
      --accent: #2f6f5e;
      --warm: #c85f37;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; }
    .shell { min-height: 100vh; display: grid; grid-template-columns: minmax(320px, 440px) 1fr; }
    aside { padding: 32px; border-right: 1px solid var(--line); background: var(--paper); }
    main { padding: 32px; display: grid; gap: 18px; align-content: start; }
    h1, h2 { margin: 0; font-weight: 650; letter-spacing: 0; }
    h1 { font-size: 24px; }
    h2 { font-size: 14px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
    p { color: var(--muted); line-height: 1.45; }
    .topline { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 6px rgba(47,111,94,.12); }
    .face { width: min(68vw, 260px); aspect-ratio: 1; border-radius: 50%; margin: 34px auto 28px; position: relative; background: #e9e2d5; border: 1px solid var(--line); box-shadow: inset 0 -22px 48px rgba(22,22,22,.06); }
    .face::after { content: ""; position: absolute; inset: 18px; border-radius: 50%; border: 1px solid rgba(22,22,22,.08); }
    .eye { position: absolute; top: 38%; width: 15%; height: 9%; border-radius: 999px; background: var(--ink); transition: transform .25s ease, height .25s ease; }
    .eye.left { left: 28%; }
    .eye.right { right: 28%; }
    .mouth { position: absolute; left: 37%; right: 37%; bottom: 31%; height: 3%; border-radius: 999px; background: var(--warm); transition: height .25s ease, bottom .25s ease; }
    .mouth.open { height: 10%; bottom: 28%; }
    .face[data-mode="speaking"] .mouth { height: 11%; bottom: 27%; animation: speak 900ms ease-in-out infinite; }
    .face[data-mode="listening"] .eye { transform: translateY(-2px); }
    .face[data-mode="thinking"] .eye.right { transform: translateY(4px); }
    @keyframes speak { 0%, 100% { transform: scaleY(.6); } 45% { transform: scaleY(1.35); } }
    .state-line { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 0 0 20px; }
    .metric { padding: 10px 0; border-top: 1px solid var(--line); }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong { display: block; min-height: 24px; font-size: 15px; font-weight: 620; overflow-wrap: anywhere; }
    .reply { min-height: 70px; padding: 18px 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); color: var(--ink); font-size: 18px; line-height: 1.4; }
    form { margin: 0; }
    .prompt { display: flex; gap: 8px; margin-top: 18px; }
    input, select { width: 100%; border: 1px solid var(--line); background: var(--field); color: var(--ink); border-radius: 6px; padding: 10px 11px; font: inherit; }
    button { border: 1px solid var(--ink); background: var(--ink); color: var(--paper); border-radius: 6px; padding: 10px 14px; font: inherit; font-weight: 620; cursor: pointer; }
    button.secondary { background: transparent; color: var(--ink); }
    .device-actions { display: flex; gap: 8px; }
    .panel { border: 1px solid var(--line); border-radius: 8px; background: var(--paper); padding: 18px; }
    .devices { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; align-items: end; }
    .device-status { margin: 10px 0 0; font-size: 13px; color: var(--muted); }
    label { display: grid; gap: 6px; color: var(--muted); font-size: 12px; }
    label span { color: var(--muted); }
    pre { margin: 0; background: #211f1b; color: #f8f3e8; border-radius: 8px; padding: 14px; overflow: auto; max-height: 42vh; font-size: 12px; line-height: 1.45; }
    @media (max-width: 860px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .devices { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
  <aside>
    <div class="topline"><h1>Mneme</h1><span class="status-dot" aria-hidden="true"></span></div>
    <div class="face" data-mode="$mode_attr" aria-label="Mneme avatar">
      <div class="eye left"></div>
      <div class="eye right"></div>
      <div class="mouth $mouth_class"></div>
    </div>
    <div class="state-line">
      <div class="metric"><span>mode</span><strong data-bind="mode">$mode</strong></div>
      <div class="metric"><span>attention</span><strong data-bind="gaze">$gaze</strong></div>
      <div class="metric"><span>expression</span><strong data-bind="expression">$expression</strong></div>
      <div class="metric"><span>voice</span><strong data-bind="voice">$voice</strong></div>
    </div>
    <div class="reply" data-bind="latest_response">$latest_response</div>
    <form class="prompt" method="post" action="/input">
      <input name="text" autocomplete="off" placeholder="Say something to Mneme">
      <button type="submit">Send</button>
    </form>
  </aside>
  <main>
    <section class="panel">
      <h2>Devices</h2>
      <form class="devices" method="post" action="/devices">
        <label><span>Camera</span>$camera_select</label>
        <label><span>Microphone</span>$microphone_select</label>
        <label><span>Speaker</span>$speaker_select</label>
        <div class="device-actions">
          <button class="secondary" type="submit" name="action" value="save">Save devices</button>
          <button class="secondary" type="submit" name="action" value="refresh">Refresh list</button>
        </div>
      </form>
      <p class="device-status" data-bind="device_status">$device_status</p>
    </section>
    <section class="panel">
      <h2>Cognition</h2>
      <div class="state-line">
        <div class="metric"><span>model</span><strong data-bind="cognition_model">$cognition_model</strong></div>
        <div class="metric"><span>status</span><strong data-bind="cognition_status">$cognition_status</strong></div>
        <div class="metric"><span>latency</span><strong data-bind="cognition_latency">$cognition_latency</strong></div>
        <div class="metric"><span>memory refs</span><strong data-bind="cognition_refs">$cognition_refs</strong></div>
      </div>
      <p class="device-status" data-bind="cognition_detail">$cognition_detail</p>
    </section>
    <section class="panel">
      <h2>Runtime</h2>
      <div class="state-line">
        <div class="metric"><span>memory rows</span><strong data-bind="memory_count">$memory_count</strong></div>
        <div class="metric"><span>last update</span><strong data-bind="timestamp">$timestamp</strong></div>
      </div>
      <pre data-bind="snapshot_json">$snapshot_json</pre>
    </section>
  </main>
  </div>
  <script>
    function value(path, fallback) {
      var current = window.mnemeState || {};
      for (var i = 0; i < path.length; i += 1) {
        if (!current || typeof current !== "object" || !(path[i] in current)) return fallback;
        current = current[path[i]];
      }
      return current == null ? fallback : current;
    }
    function setText(name, text) {
      var node = document.querySelector('[data-bind="' + name + '"]');
      if (node) node.textContent = text;
    }
    function devicesFor(kind, state) {
      var inventory = state.devices && Array.isArray(state.devices.devices) ? state.devices.devices : [];
      return inventory.filter(function (device) { return device.kind === kind; });
    }
    function renderSelect(kind, selectedId, state) {
      var select = document.querySelector('select[data-device-kind="' + kind + '"]');
      if (!select) return;
      var current = select.value || selectedId || "";
      var devices = devicesFor(kind, state);
      select.innerHTML = "";
      var auto = document.createElement("option");
      auto.value = "";
      auto.textContent = "Auto";
      select.appendChild(auto);
      devices.forEach(function (device) {
        if (!device.device_id) return;
        var option = document.createElement("option");
        option.value = String(device.device_id);
        option.textContent = String(device.label || device.device_id);
        select.appendChild(option);
      });
      if (current && !devices.some(function (device) { return device.device_id === current; })) {
        var missing = document.createElement("option");
        missing.value = current;
        missing.textContent = "Saved device unavailable (" + current + ")";
        select.appendChild(missing);
      }
      select.value = current;
    }
    function renderDevices(state) {
      var preferences = state.device_preferences || {};
      renderSelect("camera", preferences.camera_device_id, state);
      renderSelect("microphone", preferences.microphone_device_id, state);
      renderSelect("speaker", preferences.speaker_device_id, state);
      var counts = state.devices && state.devices.available_counts ? state.devices.available_counts : {};
      var total = (counts.camera || 0) + (counts.microphone || 0) + (counts.speaker || 0);
      setText(
        "device_status",
        total ? "Found " + total + " device option(s)." : "No devices found yet. Check permissions, then refresh the list."
      );
    }
    function renderState(state) {
      window.mnemeState = state;
      var avatar = value(["presence", "avatar"], {});
      var latest = value(["last_utterance", "text"], "Waiting.");
      var memory = value(["memory"], {});
      var memoryCount = Object.values(memory).reduce(function (sum, item) {
        return sum + (typeof item === "number" ? item : 0);
      }, 0);
      var face = document.querySelector(".face");
      var mode = avatar.mode || "idle";
      if (face) face.setAttribute("data-mode", mode);
      setText("mode", mode);
      setText("gaze", avatar.gaze_target || "none");
      setText("expression", avatar.expression || "neutral");
      setText("voice", value(["presence", "voice"], "default"));
      setText("latest_response", latest);
      setText("memory_count", String(memoryCount));
      setText("timestamp", String(value(["timestamp"], 0)));
      var cognition = value(["cognition"], {});
      var lastCognition = cognition.last_result || {};
      var refs = Array.isArray(lastCognition.memory_refs_used) ? lastCognition.memory_refs_used : [];
      setText("cognition_model", cognition.enabled ? String(cognition.backend || "model") + " / " + String(cognition.model || "unknown") : "off");
      setText("cognition_status", !cognition.enabled ? "deterministic" : (lastCognition.used_model ? "model-realized" : "fallback"));
      setText("cognition_latency", lastCognition.latency_ms == null ? "none" : String(lastCognition.latency_ms) + " ms");
      setText("cognition_refs", refs.length ? refs.map(function (ref) { return ref.memory_id; }).join(", ") : "none");
      setText("cognition_detail", !cognition.enabled ? "Local model wording is disabled." : (lastCognition.fallback_reason || "Local model wording is available."));
      setText("snapshot_json", JSON.stringify(state, null, 2));
      renderDevices(state);
    }
    window.mnemeState = $raw_snapshot_json;
    renderState(window.mnemeState);
    window.setInterval(function () {
      fetch("/state").then(function (response) { return response.json(); }).then(renderState).catch(function () {});
    }, 1500);
  </script>
</body>
</html>
"""


def render_snapshot_html(snapshot: dict[str, Any]) -> str:
    presence = snapshot.get("presence") if isinstance(snapshot.get("presence"), dict) else {}
    avatar = presence.get("avatar") if isinstance(presence.get("avatar"), dict) else {}
    latest = snapshot.get("last_utterance") if isinstance(snapshot.get("last_utterance"), dict) else {}
    cognition = snapshot.get("cognition") if isinstance(snapshot.get("cognition"), dict) else {}
    cognition_last = cognition.get("last_result") if isinstance(cognition.get("last_result"), dict) else {}
    preferences = snapshot.get("device_preferences") if isinstance(snapshot.get("device_preferences"), dict) else {}
    devices = _device_list(snapshot)
    mode = str(avatar.get("mode", "idle"))
    mouth = str(avatar.get("mouth_state", "closed"))
    memory = snapshot.get("memory") if isinstance(snapshot.get("memory"), dict) else {}
    memory_count = sum(value for value in memory.values() if isinstance(value, int))
    snapshot_json = json.dumps(to_jsonable(snapshot), indent=2, sort_keys=True)
    return Template(HTML_TEMPLATE).safe_substitute(
        mouth_class="open" if mouth == "open" else "",
        mode_attr=html.escape(mode, quote=True),
        mode=html.escape(mode),
        gaze=html.escape(str(avatar.get("gaze_target") or "none")),
        expression=html.escape(str(avatar.get("expression") or "neutral")),
        voice=html.escape(str(presence.get("voice") or "default")),
        latest_response=html.escape(str(latest.get("text") or "Waiting.")),
        camera_select=_device_select(
            "camera_device_id",
            "camera",
            devices,
            _optional_text(preferences.get("camera_device_id")),
        ),
        microphone_select=_device_select(
            "microphone_device_id",
            "microphone",
            devices,
            _optional_text(preferences.get("microphone_device_id")),
        ),
        speaker_select=_device_select(
            "speaker_device_id",
            "speaker",
            devices,
            _optional_text(preferences.get("speaker_device_id")),
        ),
        device_status=html.escape(_device_status_text(snapshot)),
        cognition_model=html.escape(_cognition_model_text(cognition)),
        cognition_status=html.escape(_cognition_status_text(cognition, cognition_last)),
        cognition_latency=html.escape(_cognition_latency_text(cognition_last)),
        cognition_refs=html.escape(_cognition_refs_text(cognition_last)),
        cognition_detail=html.escape(_cognition_detail_text(cognition, cognition_last)),
        memory_count=str(memory_count),
        timestamp=html.escape(str(snapshot.get("timestamp", 0))),
        snapshot_json=html.escape(snapshot_json),
        raw_snapshot_json=_script_json(snapshot),
    )


def make_ui_handler(runtime: MnemeRuntime) -> type[BaseHTTPRequestHandler]:
    class MnemeUiHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/state":
                self._send_json(runtime.snapshot())
                return
            self._send_html(render_snapshot_html(runtime.snapshot()))

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/input":
                self._handle_input()
                return
            if self.path == "/devices":
                self._handle_devices()
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def _handle_input(self) -> None:
            form = self._read_form()
            text = form.get("text", [""])[0].strip()
            if text:
                runtime.process_user_utterance(text)
            self._redirect_home()

        def _handle_devices(self) -> None:
            form = self._read_form()
            action = form.get("action", ["save"])[0]
            if action == "refresh":
                if not hasattr(runtime, "refresh_devices"):
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                runtime.refresh_devices()
                self._redirect_home()
                return
            if not hasattr(runtime, "update_device_preferences"):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            runtime.update_device_preferences(
                camera_device_id=_form_value(form, "camera_device_id"),
                microphone_device_id=_form_value(form, "microphone_device_id"),
                speaker_device_id=_form_value(form, "speaker_device_id"),
            )
            self._redirect_home()

        def _read_form(self) -> dict[str, list[str]]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            return parse_qs(raw)

        def _redirect_home(self) -> None:
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict[str, Any]) -> None:
            encoded = json.dumps(to_jsonable(payload), sort_keys=True).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return MnemeUiHandler


def make_ui_server(runtime: MnemeRuntime, *, host: str = "127.0.0.1", port: int = 8765) -> HTTPServer:
    # MnemeRuntime owns a SQLite connection created on the CLI thread. Keep the
    # local UI single-threaded so request handlers use that connection safely.
    return HTTPServer((host, port), make_ui_handler(runtime))


def serve_ui(runtime: MnemeRuntime, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = make_ui_server(runtime, host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _device_list(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    devices = snapshot.get("devices")
    if not isinstance(devices, dict):
        return []
    raw_devices = devices.get("devices", [])
    if not isinstance(raw_devices, list):
        return []
    return [dict(item) for item in raw_devices if isinstance(item, dict)]


def _device_select(
    field_name: str,
    kind: str,
    devices: list[dict[str, Any]],
    selected_id: str | None,
) -> str:
    options = [
        '<option value=""{}>Auto</option>'.format(" selected" if selected_id is None else "")
    ]
    seen_selected = selected_id is None
    for device in devices:
        if device.get("kind") != kind:
            continue
        device_id = str(device.get("device_id", ""))
        if not device_id:
            continue
        label = str(device.get("label") or device_id)
        selected = device_id == selected_id
        seen_selected = seen_selected or selected
        options.append(
            '<option value="{}"{}>{}</option>'.format(
                html.escape(device_id, quote=True),
                " selected" if selected else "",
                html.escape(label),
            )
        )
    if selected_id is not None and not seen_selected:
        options.append(
            '<option value="{}" selected>{}</option>'.format(
                html.escape(selected_id, quote=True),
                html.escape(f"Saved device unavailable ({selected_id})"),
            )
        )
    return '<select name="{}" data-device-kind="{}">{}</select>'.format(
        html.escape(field_name, quote=True),
        html.escape(kind, quote=True),
        "".join(options),
    )


def _device_status_text(snapshot: dict[str, Any]) -> str:
    devices = snapshot.get("devices")
    if not isinstance(devices, dict):
        return "No device scan has run yet. Refresh the list."
    counts = devices.get("available_counts")
    if not isinstance(counts, dict):
        return "No devices found yet. Check permissions, then refresh the list."
    total = sum(value for value in counts.values() if isinstance(value, int))
    if total:
        return f"Found {total} device option(s)."
    return "No devices found yet. Check permissions, then refresh the list."


def _cognition_model_text(cognition: dict[str, Any]) -> str:
    if not cognition.get("enabled"):
        return "off"
    backend = cognition.get("backend") or "model"
    model = cognition.get("model") or "unknown"
    return f"{backend} / {model}"


def _cognition_status_text(cognition: dict[str, Any], last_result: dict[str, Any]) -> str:
    if not cognition.get("enabled"):
        return "deterministic"
    if not last_result:
        return "ready"
    return "model-realized" if last_result.get("used_model") else "fallback"


def _cognition_latency_text(last_result: dict[str, Any]) -> str:
    latency = last_result.get("latency_ms")
    return f"{latency} ms" if isinstance(latency, int) else "none"


def _cognition_refs_text(last_result: dict[str, Any]) -> str:
    refs = last_result.get("memory_refs_used")
    if not isinstance(refs, list) or not refs:
        return "none"
    memory_ids = [
        str(ref.get("memory_id"))
        for ref in refs
        if isinstance(ref, dict) and ref.get("memory_id")
    ]
    return ", ".join(memory_ids) if memory_ids else "none"


def _cognition_detail_text(cognition: dict[str, Any], last_result: dict[str, Any]) -> str:
    if not cognition.get("enabled"):
        return "Local model wording is disabled."
    if not last_result:
        return "Local model wording is enabled."
    fallback = last_result.get("fallback_reason")
    return f"Fallback: {fallback}" if fallback else "Local model wording was used for the last response."


def _form_value(form: dict[str, list[str]], key: str) -> str | None:
    values = form.get(key, [""])
    value = values[0].strip() if values else ""
    return value or None


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _script_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True).replace("</", "<\\/")
