from __future__ import annotations

import html
import json
import mimetypes
import queue
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from aether.evaluation.scorecard import SCORECARD, Ledger
from aether.recording.replay import list_runs, merged, summarize
from aether.runtime.events import EventBus
from aether.runtime.lifecycle import Runtime

REPO = Path(__file__).resolve().parents[3]


class CommandCenter:
    def __init__(
        self,
        bus: EventBus,
        runtime: Runtime | None,
        runs_root: str | Path,
        ledger: Ledger,
        host="127.0.0.1",
        port=8765,
    ):
        self.bus, self.runtime, self.runs_root, self.ledger = bus, runtime, Path(runs_root), ledger
        self.recent: deque = deque(maxlen=500)
        self.sub = bus.subscribe("*")
        self.host, self.port = host, port
        self._srv: ThreadingHTTPServer | None = None

    def _safe_run_dir(self, run_id: str) -> Path | None:
        if not run_id or run_id in {".", ".."} or "/" in run_id or "\\" in run_id:
            return None
        root = self.runs_root.resolve()
        candidate = (root / run_id).resolve()
        return candidate if candidate.is_relative_to(root) else None

    def _run_detail(self, run_id: str) -> dict | None:
        directory = self._safe_run_dir(run_id)
        if directory is None or not directory.is_dir():
            return None
        manifest_path = directory / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = None
        summary = summarize(directory)
        stream_counts = {
            path.stem: sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
            for path in sorted((directory / "streams").glob("*.jsonl"))
        } if (directory / "streams").is_dir() else {}
        verdict_path = Path("evidence/E-10") / f"{run_id}.json"
        try:
            verdict = json.loads(verdict_path.read_text(encoding="utf-8")) if verdict_path.is_file() else None
        except (OSError, json.JSONDecodeError):
            verdict = {"status": "FAILED", "error": "verdict file is unreadable"}
        return {
            "run_id": run_id,
            "manifest": manifest,
            "stream_counts": stream_counts,
            "summary": summary,
            "verify_run": verdict,
        }

    def _timeline(self, run_id: str) -> list[dict] | None:
        directory = self._safe_run_dir(run_id)
        if directory is None or not directory.is_dir():
            return None
        items = [
            {"t_mono": stamp, "stream": stream, "record": record}
            for stamp, stream, record in merged(directory)
        ]
        events_path = directory / "events.jsonl"
        if events_path.is_file():
            with events_path.open(encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        event = json.loads(line)
                        items.append(
                            {"t_mono": float(event.get("t_mono", 0)), "stream": "event", "record": event}
                        )
        return sorted(items, key=lambda item: item["t_mono"])

    @staticmethod
    def _page(title: str, body: str, script: str = "") -> bytes:
        source = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="/design/tokens.css"><link rel="stylesheet" href="/design/components.css">
<style>
body{{margin:0;padding:clamp(12px,3vw,24px);font:14px system-ui,sans-serif;background:var(--color-bg,#101318);color:var(--color-fg,#eee)}}
main{{max-width:1100px;margin:auto}}nav{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
a{{color:var(--color-accent,#83b7ff)}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;max-height:50vh;overflow:auto}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:7px;border-bottom:1px solid #555;text-align:left;vertical-align:top}}
.empty{{opacity:.65}}img{{max-width:100%;height:auto}}.null-banner{{padding:14px;background:#692b24;color:#fff;font-weight:700}}
.columns{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}.panel{{border:1px solid #555;border-radius:8px;padding:10px;min-width:0}}
@media(max-width:640px){{.columns{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main><nav><a href="/">Home</a><a href="/scorecard">Scorecard</a><a href="/overlay">Overlay</a><a href="/calibrate">Calibrate</a></nav>
<h1>{html.escape(title)}</h1>{body}</main><script>{script}</script></body></html>"""
        return source.encode("utf-8")

    def _scorecard_data(self) -> dict:
        latest = self.ledger.latest()
        for criterion in SCORECARD:
            latest[criterion.id]["proposed_threshold"] = criterion.proposed_threshold
            latest[criterion.id]["threshold_status"] = "PROPOSED, NOT FROZEN"
        return latest

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
            def log_message(self, *args):
                pass

            def _json(self, obj, code=200):
                body = json.dumps(obj, default=str).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _bytes(self, body: bytes, content_type: str, code=200):
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _file(self, path: Path):
                if not path.is_file():
                    return self._json({"error": "not found"}, 404)
                return self._bytes(path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")

            def do_GET(self):
                path = self.path.split("?", 1)[0]
                if path == "/":
                    return self._file(REPO / "interfaces/command-center/index.html")
                if path == "/calibrate":
                    return self._file(REPO / "interfaces/command-center/calibrate.html")
                if path == "/scorecard":
                    body = '<p class="empty">Proposed thresholds are not frozen.</p><div id="score">loading…</div>'
                    script = """fetch('/api/scorecard').then(r=>r.json()).then(data=>{
const rows=Object.values(data);document.getElementById('score').innerHTML='<table><tr><th>ID</th><th>Criterion</th><th>Status</th><th>Value</th><th>Proposed threshold</th><th>Evidence</th></tr>'+
rows.map(x=>'<tr><td>'+x.criterion+'</td><td>'+x.title+'</td><td>'+x.status+'</td><td>'+(x.value||'no data')+'</td><td>'+x.proposed_threshold+'<br>'+x.threshold_status+'</td><td>'+(x.evidence||'no data')+'</td></tr>').join('')+'</table>';});"""
                    return self._bytes(cc._page("Engineering scorecard", body, script), "text/html; charset=utf-8")
                if path == "/overlay":
                    body = '<div id="null" class="null-banner" hidden>NULL BACKEND — no model running</div><div class="columns"><section class="panel"><h2>Supervisor assessment</h2><pre id="assessment" class="empty">no data</pre></section><section class="panel"><h2>Reflex chunk</h2><pre id="reflex" class="empty">no data</pre></section></div>'
                    script = """async function refresh(){const events=await fetch('/api/events').then(r=>r.json());const a=[...events].reverse().find(e=>e.topic==='supervisor.assessment');const r=[...events].reverse().find(e=>e.topic==='reflex.chunk');document.getElementById('assessment').textContent=a?JSON.stringify({phase:a.phase,objective:a.objective,explanation:a.explanation,confidence:a.confidence,accepted:a.accepted},null,2):'no data';document.getElementById('reflex').textContent=r?JSON.stringify({backend:r.backend,goal:r.goal,latency_ms:r.latency_ms,n_sent:r.n_sent,stalled:r.stalled},null,2):'no data';document.getElementById('null').hidden=!(r&&r.backend==='null');}refresh();setInterval(refresh,500);"""
                    return self._bytes(cc._page("Live companion overlay", body, script), "text/html; charset=utf-8")
                if path.startswith("/runs/"):
                    run_id = path[len("/runs/") :]
                    if cc._safe_run_dir(run_id) is None:
                        return self._json({"error": "not found"}, 404)
                    body = '<pre id="run" class="empty">loading…</pre>'
                    script = f"""fetch('/api/runs/'+encodeURIComponent({json.dumps(run_id)})).then(r=>r.json()).then(d=>document.getElementById('run').textContent=JSON.stringify(d,null,2));"""
                    return self._bytes(cc._page(f"Run {run_id}", body, script), "text/html; charset=utf-8")
                if path.startswith("/replay/"):
                    run_id = path[len("/replay/") :]
                    if cc._safe_run_dir(run_id) is None:
                        return self._json({"error": "not found"}, 404)
                    body = """<input id="scrub" type="range" min="0" max="0" value="0" style="width:100%"><p id="position">no data</p><img id="frame" alt="Recorded frame"><div class="columns"><section class="panel"><h2>Intended</h2><pre id="intended">no data</pre></section><section class="panel"><h2>Commanded</h2><pre id="commanded">no data</pre></section><section class="panel"><h2>Delivered</h2><pre id="delivered">no data</pre></section><section class="panel"><h2>Observed</h2><pre id="observed">no data</pre></section></div><h2>Events at frame time</h2><pre id="events">no data</pre>"""
                    script = f"""const id={json.dumps(run_id)};let rows=[],frames=[];const esc=x=>JSON.stringify(x,null,2);fetch('/api/runs/'+encodeURIComponent(id)+'/timeline').then(r=>r.json()).then(data=>{{rows=data;frames=rows.filter(x=>x.stream==='frame');const slider=document.getElementById('scrub');slider.max=Math.max(0,frames.length-1);slider.oninput=show;show();}});function show(){{if(!frames.length)return;const f=frames[Number(document.getElementById('scrub').value)];const rec=f.record;document.getElementById('position').textContent='t_mono '+f.t_mono;document.getElementById('frame').src='/api/runs/'+encodeURIComponent(id)+'/frames/'+encodeURIComponent(String(rec.seq).padStart(8,'0')+'.jpg');for(const name of ['intended','commanded','delivered','observed']){{const row=rows.filter(x=>x.stream===name&&Math.abs(x.t_mono-f.t_mono)<0.5).map(x=>x.record);document.getElementById(name).textContent=row.length?esc(row):'no data';}}const ev=rows.filter(x=>x.stream==='event'&&Math.abs(x.t_mono-f.t_mono)<0.5).map(x=>x.record);document.getElementById('events').textContent=ev.length?esc(ev):'no data';}}"""
                    return self._bytes(cc._page(f"Replay {run_id}", body, script), "text/html; charset=utf-8")
                if path.startswith("/design/"):
                    base = (REPO / "interfaces/shared/design").resolve()
                    target = (base / path[len("/design/") :]).resolve()
                    return self._file(target) if target.is_relative_to(base) else self._json({"error": "forbidden"}, 403)
                parts = path.strip("/").split("/")
                if len(parts) >= 3 and parts[:2] == ["api", "runs"]:
                    run_id = parts[2]
                    directory = cc._safe_run_dir(run_id)
                    if directory is None or not directory.is_dir():
                        return self._json({"error": "not found"}, 404)
                    if len(parts) == 3:
                        detail = cc._run_detail(run_id)
                        return self._json(detail) if detail is not None else self._json({"error": "not found"}, 404)
                    if len(parts) == 4 and parts[3] == "timeline":
                        try:
                            timeline = cc._timeline(run_id)
                        except (OSError, json.JSONDecodeError, ValueError) as exc:
                            return self._json({"error": str(exc)}, 500)
                        return self._json(timeline) if timeline is not None else self._json({"error": "not found"}, 404)
                    if len(parts) == 5 and parts[3] == "frames":
                        filename = parts[4]
                        if Path(filename).name != filename or not filename.lower().endswith(".jpg"):
                            return self._json({"error": "not found"}, 404)
                        return self._file(directory / "frames" / filename)
                if path == "/api/health":
                    return self._json(cc.runtime.health() if cc.runtime else {})
                if path == "/api/runs":
                    return self._json(list_runs(cc.runs_root))
                if path == "/api/scorecard":
                    return self._json(cc._scorecard_data())
                if path == "/api/events":
                    return self._json(list(cc.recent)[-200:])
                return self._json({"error": "not found"}, 404)

        self._srv = ThreadingHTTPServer((self.host, self.port), H)
        threading.Thread(target=self._drain, daemon=True).start()
        self._srv.serve_forever()

    def shutdown(self) -> None:
        if self._srv:
            self._srv.shutdown()
            self._srv.server_close()
            self._srv = None
