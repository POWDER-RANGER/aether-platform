# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Recording session on disk.

runs/<run_id>/
  manifest.json          RunIdentity + settings hash + start/stop + stream index
  events.jsonl           everything on the bus (lifecycle, governor decisions, perception, plans)
  streams/<name>.jsonl   intended | commanded | delivered | observed | player_input (kept distinct, §5)
  frames/<seq>.jpg       sampled frames; frames.jsonl maps seq -> t_mono, size
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import numpy as np

from aether.runtime.events import EventBus, JsonlSink
from aether.runtime.identity import RunIdentity

STREAMS = ("intended", "commanded", "delivered", "observed", "player_input")


class RecordingSession:
    def __init__(
        self, root: str | Path, identity: RunIdentity, bus: EventBus, frame_every_n: int = 6, jpeg_quality: int = 85
    ):
        self.identity = identity
        self.dir = Path(root) / identity.run_id
        self.bus = bus
        self.frame_every_n = max(1, frame_every_n)
        self.jpeg_quality = jpeg_quality
        self._frame_n = 0
        self._lock = threading.Lock()
        self._streams: dict[str, object] = {}
        self._sink: JsonlSink | None = None
        self.started = self.stopped = None

    def start(self) -> None:
        (self.dir / "streams").mkdir(parents=True, exist_ok=True)
        (self.dir / "frames").mkdir(exist_ok=True)
        for s in STREAMS:
            self._streams[s] = (self.dir / "streams" / f"{s}.jsonl").open("a", encoding="utf-8")
        self._frames_index = (self.dir / "frames.jsonl").open("a", encoding="utf-8")
        self._sink = JsonlSink(self.bus, self.dir / "events.jsonl", "*")
        self._sink.start()
        self.started = time.time()
        self._write_manifest()
        self.bus.publish("recording.started", run_id=self.identity.run_id, dir=str(self.dir))

    def record(self, stream: str, t_mono: float, **data) -> None:
        if stream not in STREAMS:
            raise ValueError(f"unknown stream {stream}")
        line = json.dumps({"t_mono": t_mono, **data}, default=str, separators=(",", ":"))
        with self._lock:
            f = self._streams[stream]
            f.write(line + "\n")  # type: ignore[attr-defined]

    def frame(self, t_mono: float, img: np.ndarray) -> None:
        self._frame_n += 1
        if self._frame_n % self.frame_every_n:
            return
        from PIL import Image

        seq = self._frame_n
        Image.fromarray(img).save(self.dir / "frames" / f"{seq:08d}.jpg", quality=self.jpeg_quality)
        with self._lock:
            self._frames_index.write(
                json.dumps({"seq": seq, "t_mono": t_mono, "h": img.shape[0], "w": img.shape[1]}) + "\n"
            )

    def stop(self) -> None:
        self.stopped = time.time()
        self.bus.publish("recording.stopped", run_id=self.identity.run_id)
        if self._sink:
            self._sink.stop()
        with self._lock:
            for f in self._streams.values():
                f.close()  # type: ignore[attr-defined]
            self._frames_index.close()
        self._write_manifest()

    def _write_manifest(self) -> None:
        m = {
            "identity": self.identity.to_dict(),
            "started": self.started,
            "stopped": self.stopped,
            "streams": list(STREAMS),
            "frame_every_n": self.frame_every_n,
            "format_version": 1,
        }
        (self.dir / "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
