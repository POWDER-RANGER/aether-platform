# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Timestamped ring buffer of full captured frames (retain full frame, §6)."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Frame:
    seq: int
    t_mono: float
    image: np.ndarray  # HxWx3 uint8 RGB, full resolution
    source: str = "dxcam"


class FrameBuffer:
    def __init__(self, capacity: int = 120):
        self._d: deque[Frame] = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._seq = 0

    def push(self, t_mono: float, image: np.ndarray, source: str = "dxcam") -> Frame:
        with self._cv:
            self._seq += 1
            f = Frame(self._seq, t_mono, image, source)
            self._d.append(f)
            self._cv.notify_all()
            return f

    def latest(self) -> Frame | None:
        with self._lock:
            return self._d[-1] if self._d else None

    def wait_newer(self, seq: int, timeout: float) -> Frame | None:
        with self._cv:
            self._cv.wait_for(lambda: self._d and self._d[-1].seq > seq, timeout=timeout)
            return self._d[-1] if self._d and self._d[-1].seq > seq else None

    def window(self, seconds: float) -> list[Frame]:
        with self._lock:
            if not self._d:
                return []
            t_end = self._d[-1].t_mono
            return [f for f in self._d if f.t_mono >= t_end - seconds]
