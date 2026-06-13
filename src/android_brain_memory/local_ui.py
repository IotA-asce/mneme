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
      color-scheme: light dark;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #111827;
      color: #f9fafb;
    }
    body { margin: 0; min-height: 100vh; display: grid; grid-template-columns: minmax(260px, 420px) 1fr; }
    main { padding: 28px; }
    aside { padding: 28px; background: #0f172a; border-right: 1px solid #334155; }
    .face { width: 220px; height: 220px; border-radius: 50%; background: #1f2937; margin: 20px auto; position: relative; border: 4px solid #38bdf8; }
    .eye { position: absolute; top: 78px; width: 28px; height: 18px; border-radius: 50%; background: #f8fafc; }
    .eye.left { left: 58px; }
    .eye.right { right: 58px; }
    .mouth { position: absolute; left: 72px; right: 72px; bottom: 58px; height: 12px; border-radius: 999px; background: #f97316; }
    .mouth.open { height: 28px; bottom: 50px; }
    .pill { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #1e293b; border: 1px solid #475569; margin: 2px 4px 2px 0; }
    form { display: flex; gap: 8px; margin-top: 18px; }
    input { flex: 1; padding: 10px 12px; border-radius: 6px; border: 1px solid #475569; background: #020617; color: #f8fafc; }
    button { padding: 10px 14px; border-radius: 6px; border: 0; background: #38bdf8; color: #082f49; font-weight: 700; }
    pre { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 14px; overflow: auto; max-height: 70vh; }
    @media (max-width: 800px) { body { grid-template-columns: 1fr; } aside { border-right: 0; border-bottom: 1px solid #334155; } }
  </style>
</head>
<body>
  <aside>
    <h1>Mneme</h1>
    <div class="face" aria-label="Mneme avatar">
      <div class="eye left"></div>
      <div class="eye right"></div>
      <div class="mouth $mouth_class"></div>
    </div>
    <p><span class="pill">mode: $mode</span><span class="pill">gaze: $gaze</span></p>
    <p><span class="pill">expression: $expression</span><span class="pill">blink: $blink</span></p>
    <p>$latest_response</p>
    <form method="post" action="/input">
      <input name="text" autocomplete="off" placeholder="Say something to Mneme">
      <button type="submit">Send</button>
    </form>
  </aside>
  <main>
    <h2>Runtime State</h2>
    <pre>$snapshot_json</pre>
  </main>
</body>
</html>
"""


def render_snapshot_html(snapshot: dict[str, Any]) -> str:
    presence = snapshot.get("presence") if isinstance(snapshot.get("presence"), dict) else {}
    avatar = presence.get("avatar") if isinstance(presence.get("avatar"), dict) else {}
    latest = snapshot.get("last_utterance") if isinstance(snapshot.get("last_utterance"), dict) else {}
    mode = str(avatar.get("mode", "idle"))
    mouth = str(avatar.get("mouth_state", "closed"))
    return Template(HTML_TEMPLATE).safe_substitute(
        mouth_class="open" if mouth == "open" else "",
        mode=html.escape(mode),
        gaze=html.escape(str(avatar.get("gaze_target") or "none")),
        expression=html.escape(str(avatar.get("expression") or "neutral")),
        blink=html.escape(str(avatar.get("blink_pattern") or "idle")),
        latest_response=html.escape(str(latest.get("text") or "Waiting.")),
        snapshot_json=html.escape(json.dumps(to_jsonable(snapshot), indent=2, sort_keys=True)),
    )


def make_ui_handler(runtime: MnemeRuntime) -> type[BaseHTTPRequestHandler]:
    class MnemeUiHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/state":
                self._send_json(runtime.snapshot())
                return
            self._send_html(render_snapshot_html(runtime.snapshot()))

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/input":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            text = parse_qs(raw).get("text", [""])[0].strip()
            if text:
                runtime.process_user_utterance(text)
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
