# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Command Center HTTP server (stdlib only). Binds 127.0.0.1. Read-only: status, runs, scorecard, live events.

GET /                 -> interfaces/command-center/index.html
GET /design/*         -> interfaces/shared/design/*
GET /api/health       -> runtime component health
GET /api/runs         -> recordings list
GET /api/runs/<id>    -> run summary
GET /api/scorecard    -> E-01..E-10 latest results
GET /api/events       -> last N bus events (ring buffer)
No endpoint can command the controller (Governor is sole authority; STOP stays the file/hotkey path).
"""

from __future__ import annotations

import json
import mimetypes
import queue
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from aether.evaluation.scorecard import Ledger
from aether.recording.replay import list_runs, summarize
from aether.runtime.lifecycle import Runtime
from aether.runtime.topics import TopicBus

REPO = Path(__file__).resolve().parents[3]


class CommandCenter:
    def __init__(
        self, bus: TopicBus, runtime: Runtime | None, runs_root: str | Path, ledger: Ledger, host="127.0.0.1", port=8765
    ):
        self.bus, self.runtime, self.runs_root, self.ledger = bus, runtime, Path(runs_root), ledger
        self.recent: deque = deque(maxlen=500)
        self.sub = bus.subscribe("*")
        self.host, self.port = host, port
        self._srv: ThreadingHTTPServer | None = None

    def _drain(self) -> None:
        while True:
            try:
                self.recent.append(self.sub.q.get(timeout=0.5))
            except queue.Empty:
                if self._srv is None:
                    return

    def serve_forever(self) -> None:
        cc = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, obj, code=200):
                b = json.dumps(obj, default=str).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def _file(self, p: Path):
                if not p.is_file():
                    return self._json({"error": "not found"}, 404)
                b = p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(p.name)[0] or "application/octet-stream")
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    return self._file(REPO / "interfaces/command-center/index.html")
                if path.startswith("/design/"):
                    base = (REPO / "interfaces/shared/design").resolve()
                    p = (base / path[len("/design/") :]).resolve()
                    return self._file(p) if str(p).startswith(str(base)) else self._json({"error": "forbidden"}, 403)
                if path == "/api/health":
                    return self._json(cc.runtime.health() if cc.runtime else {})
                if path == "/api/runs":
                    return self._json(list_runs(cc.runs_root))
                if path.startswith("/api/runs/"):
                    rid = path.rsplit("/", 1)[-1]
                    d = (cc.runs_root / rid).resolve()
                    if not str(d).startswith(str(cc.runs_root.resolve())) or not d.exists():
                        return self._json({"error": "not found"}, 404)
                    return self._json(summarize(d))
                if path == "/api/scorecard":
                    return self._json(cc.ledger.latest())
                if path == "/api/events":
                    return self._json(list(cc.recent)[-200:])
                return self._json({"error": "not found"}, 404)

        self._srv = ThreadingHTTPServer((self.host, self.port), H)
        threading.Thread(target=self._drain, daemon=True).start()
        self._srv.serve_forever()

    def shutdown(self) -> None:
        if self._srv:
            self._srv.shutdown()
            self._srv = None
