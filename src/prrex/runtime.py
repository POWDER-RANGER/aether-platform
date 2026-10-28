# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""PR-REX companion loop.

Two pathways (§6): the reflex thread consumes the latest 256x256 view and sends signed intent chunks to the
Governor; the supervisor thread runs slow VLM assessment and updates the plan. They share only the Planner
goal string and WorldState — the reflex thread never waits on the supervisor.

Receding horizon: each reflex chunk is truncated to execute_fraction before sending; the next chunk is
requested from a fresh observation. All controller output goes through GovernorClient (Governor is sole authority).
"""

from __future__ import annotations

import threading
import time

from aether.control.client import GovernorClient
from aether.control.intent import Source
from aether.perception.frame_buffer import FrameBuffer
from aether.perception.pipeline import PerceptionPipeline
from aether.perception.preprocess import reflex_view, roi_crop
from aether.recording.session import RecordingSession
from aether.runtime.events import EventBus
from aether.runtime.lifecycle import ThreadedComponent
from prrex.backends.base import ReflexBackend, SupervisorBackend
from prrex.supervisor.planner import Planner
from prrex.supervisor.recovery import StallDetector


class ReflexLoop(ThreadedComponent):
    name = "prrex.reflex"

    def __init__(
        self,
        bus: EventBus,
        buf: FrameBuffer,
        backend: ReflexBackend,
        client: GovernorClient,
        planner: Planner,
        perception: PerceptionPipeline,
        rec: RecordingSession | None,
        chunk_len: int = 16,
        execute_fraction: float = 0.5,
        view_size: int = 256,
    ):
        super().__init__(bus)
        self.buf, self.backend, self.client, self.planner, self.perception, self.rec = (
            buf,
            backend,
            client,
            planner,
            perception,
            rec,
        )
        self.chunk_len, self.exec_frac, self.view_size = chunk_len, execute_fraction, view_size
        self.stall = StallDetector()
        self._last_seq = 0

    def loop_once(self) -> None:
        f = self.buf.wait_newer(self._last_seq, timeout=0.5)
        if f is None:
            return
        self._last_seq = f.seq
        ws = self.perception.process(f)
        goal = self.planner.step(ws)
        out = self.backend.act(reflex_view(f.image, self.view_size), goal, self.chunk_len)
        n = max(1, int(round(len(out.frames) * self.exec_frac)))
        frames = out.frames[:n]
        # 120 Hz output tick; 400 ms intent TTL (architectural targets, §6). REFINE: take both from control settings.
        self.client.send_frames(
            frames,
            frame_dt_ms=1000.0 / 120.0,
            ttl_ms=400,
            confidence=out.confidence,
            note=f"{out.backend} goal={goal!r}"[:200],
        )
        moving = any(abs(fr.lx) + abs(fr.ly) > 0.3 for fr in frames)
        stalled = self.stall.update(f, moving)
        ev = dict(
            backend=out.backend,
            latency_ms=round(out.latency_ms, 1),
            n_sent=n,
            goal=goal,
            frame_seq=f.seq,
            stalled=stalled,
        )
        self.bus.publish("reflex.chunk", **ev)
        if self.rec:
            self.rec.record("intended", f.t_mono, **ev, frames=[fr.to_dict() for fr in frames])
            self.rec.frame(f.t_mono, f.image)
        if stalled:
            self.planner.s.replan_requested = True
            self.bus.publish("recovery.stall", frame_seq=f.seq)


class SupervisorLoop(ThreadedComponent):
    name = "prrex.supervisor"

    def __init__(
        self,
        bus: EventBus,
        buf: FrameBuffer,
        backend: SupervisorBackend,
        planner: Planner,
        perception: PerceptionPipeline,
        rois: dict,
        player_goal: str | None,
        period_s: float = 2.0,
    ):
        super().__init__(bus)
        self.buf, self.backend, self.planner, self.perception = buf, backend, planner, perception
        self.rois, self.player_goal, self.period_s = rois, player_goal, period_s

    def loop_once(self) -> None:
        f = self.buf.latest()
        if f is None or not (self.planner.s.replan_requested or self.planner.s.active is None):
            return
        crops = {k: roi_crop(f.image, tuple(v)) for k, v in self.rois.items()} or {"full": f.image}
        out = self.backend.assess(crops, self.perception.state.summary_text(), self.player_goal, self.planner.s.history)
        accepted = self.planner.apply(out)
        self.bus.publish(
            "supervisor.assessment",
            backend=out.backend,
            phase=out.phase,
            objective=out.objective,
            subgoals=[s.text for s in out.subgoals],
            explanation=out.explanation,
            confidence=out.confidence,
            latency_ms=round(out.latency_ms, 1),
            accepted=accepted,
            frame_seq=f.seq,
        )


def build_client(endpoint: str, key: bytes) -> GovernorClient:
    return GovernorClient(endpoint, key, Source.REFLEX)


_ = (threading, time)
