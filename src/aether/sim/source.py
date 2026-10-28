"""Threaded synthetic capture source. Emits synthetic frames and capture.heartbeat events."""

from __future__ import annotations

import time

from aether.perception.frame_buffer import FrameBuffer
from aether.runtime.lifecycle import ThreadedComponent
from aether.runtime.topics import TopicBus

from .scene import SyntheticScene


class SyntheticSource(ThreadedComponent):
    name = "capture.synthetic"

    def __init__(self, bus: TopicBus, buf: FrameBuffer, fps: float = 30.0, seed: int = 7):
        if fps <= 0:
            raise ValueError("fps must be positive")
        super().__init__(bus)
        self.buf, self.period_s = buf, 1.0 / fps
        self.scene = SyntheticScene(seed=seed)
        self.started_at = 0.0
        self.seq = 0

    def start(self) -> None:
        self.started_at = time.monotonic()
        super().start()

    def loop_once(self) -> None:
        now = time.monotonic()
        elapsed = now - self.started_at
        self.seq += 1
        frame = self.scene.frame(self.seq, elapsed)
        pushed = self.buf.push(now, frame, "synthetic")
        self.bus.publish("capture.heartbeat", seq=pushed.seq, shape=list(frame.shape), source="synthetic")
