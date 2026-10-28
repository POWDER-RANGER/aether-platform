# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Capture sources feeding the FrameBuffer. DxcamSource wraps the ported capture (screen.py, UNVERIFIED here);
FileSource replays recorded frames for offline perception work — labelled as replay, never live (§10)."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from aether.perception.frame_buffer import FrameBuffer
from aether.runtime.events import EventBus
from aether.runtime.lifecycle import ThreadedComponent


class DxcamSource(ThreadedComponent):
    name = "capture.dxcam"

    def __init__(self, bus: EventBus, buf: FrameBuffer, process_name: str, fps: int = 60):
        super().__init__(bus)
        self.buf, self.process_name, self.period_s = buf, process_name, 1.0 / fps
        self._cam = None
        self._region = None

    def start(self) -> None:
        import dxcam

        from .screen import find_window_rect

        self._region = find_window_rect(self.process_name)
        self._cam = dxcam.create(output_color="RGB")
        super().start()

    def loop_once(self) -> None:
        img = self._cam.grab(region=self._region)
        if img is not None:
            f = self.buf.push(time.monotonic(), img, "dxcam")
            if f.seq % 60 == 0:
                self.bus.publish("capture.heartbeat", seq=f.seq, shape=list(img.shape))

    def stop(self) -> None:
        super().stop()
        self._cam = None


class FileSource(ThreadedComponent):
    name = "capture.replay"

    def __init__(self, bus: EventBus, buf: FrameBuffer, frames_dir: str | Path, fps: float = 10.0, loop: bool = False):
        super().__init__(bus)
        self.buf, self.period_s, self.loop = buf, 1.0 / fps, loop
        self.files = sorted(Path(frames_dir).glob("*.jpg")) + sorted(Path(frames_dir).glob("*.png"))
        self.i = 0

    def loop_once(self) -> None:
        from PIL import Image

        if self.i >= len(self.files):
            if not self.loop:
                self._stop.set()
                return
            self.i = 0
        img = np.asarray(Image.open(self.files[self.i]).convert("RGB"))
        self.i += 1
        self.buf.push(time.monotonic(), img, "replay")
