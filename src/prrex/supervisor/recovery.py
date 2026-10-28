# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Stall / stuck detection (also the diagnostic hook for previously observed gameplay stalls, M1).
Flags when the screen stops changing while the companion is commanding motion."""
from __future__ import annotations

from collections import deque

from aether.perception.frame_buffer import Frame
from aether.perception.preprocess import frame_change


class StallDetector:
    def __init__(self, window_s: float = 3.0, change_threshold: float = 0.01):
        self.window_s, self.thr = window_s, change_threshold
        self.samples: deque[tuple[float, float, bool]] = deque()  # (t, change, commanding_motion)
        self._prev: Frame | None = None

    def update(self, frame: Frame, commanding_motion: bool) -> bool:
        if self._prev is not None:
            self.samples.append((frame.t_mono, frame_change(self._prev.image, frame.image), commanding_motion))
        self._prev = frame
        while self.samples and frame.t_mono - self.samples[0][0] > self.window_s:
            self.samples.popleft()
        if len(self.samples) < 5:
            return False
        moving = [c for _, c, m in self.samples if m]
        return len(moving) >= 0.8 * len(self.samples) and max(moving, default=1.0) < self.thr
