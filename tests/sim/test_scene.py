from __future__ import annotations

import json
import time

import numpy as np

from aether.bench import verify_run
from aether.perception.frame_buffer import FrameBuffer
from aether.perception.pipeline import PerceptionPipeline
from aether.perception.preprocess import roi_crop
from aether.perception.readers import BarReader
from aether.recording.session import RecordingSession
from aether.runtime.identity import RunIdentity
from aether.runtime.topics import TopicBus
from aether.sim.scene import SyntheticScene
from aether.sim.source import SyntheticSource
from prrex.backends.base import NullReflex, NullSupervisor, Subgoal, SupervisorOutput
from prrex.runtime import ReflexLoop, SupervisorLoop
from prrex.supervisor.planner import Planner


class FakeGovernorClient:
    """Test double for the Governor client boundary; it never emits controller output."""

    def __init__(self, recording):
        self.recording = recording
        self.calls = 0

    def send_frames(self, frames, **kwargs):
        self.calls += 1
        stamp = time.monotonic()
        for stream in ("commanded", "delivered", "observed"):
            self.recording.record(stream, stamp, synthetic=True, frame_count=len(frames), client="fake-governor")
        return self.calls


class FixedPlanSupervisor(NullSupervisor):
    name = "synthetic-fixed-plan"

    def assess(self, rois, world_text, player_goal, history):
        return SupervisorOutput(
            "synthetic-phase",
            "synthetic-objective",
            [Subgoal("hold synthetic objective")],
            "fixed synthetic plan",
            1.0,
            0.0,
            self.name,
        )


def test_scene_is_deterministic_and_health_schedule_is_readable():
    a, b = SyntheticScene(seed=11), SyntheticScene(seed=11)
    reader = BarReader("health", (40, 220, 80), tol=8, min_conf_pixels=1)
    for seq in range(1, 31):
        elapsed = seq / 10
        frame = a.frame(seq, elapsed)
        assert np.array_equal(frame, b.frame(seq, elapsed))
        crop = roi_crop(frame, (12 / 320, 12 / 180, 112 / 320, 22 / 180))
        fact = reader.read(crop, elapsed, seq)
        assert fact is not None
        assert abs(float(fact.value) - a.health_ratio(elapsed)) <= 0.05


def run_pipeline(tmp_path, supervisor_backend):
    bus, buffer = TopicBus(), FrameBuffer(512)
    identity = RunIdentity(run_id="headless-" + supervisor_backend.name.replace("-", "_"))
    recording = RecordingSession(tmp_path, identity, bus, frame_every_n=2)
    recording.start()
    source = SyntheticSource(bus, buffer, fps=30, seed=5)
    planner = Planner()
    perception = PerceptionPipeline(bus, {}, {})
    client = FakeGovernorClient(recording)
    reflex = ReflexLoop(bus, buffer, NullReflex(), client, planner, perception, recording, chunk_len=4)
    supervisor = SupervisorLoop(bus, buffer, supervisor_backend, planner, perception, {}, None, period_s=0.05)
    source.start()
    reflex.start()
    supervisor.start()
    deadline = time.monotonic() + 3.0
    try:
        while time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        supervisor.stop()
        reflex.stop()
        source.stop()
        recording.stop()
    run = tmp_path / identity.run_id
    result = verify_run(run, tmp_path / "verification")
    assert result["status"] == "VERIFIED", result
    assert client.calls > 0
    for stream in ("intended", "commanded", "delivered", "observed"):
        assert (run / "streams" / f"{stream}.jsonl").stat().st_size > 0
    rows = [json.loads(line) for line in (run / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    disk = {int(path.stem) for path in (run / "frames").glob("*.jpg")}
    assert {row["seq"] for row in rows} == disk


def test_reflex_supervisor_recording_pipeline_with_null_supervisor(tmp_path):
    run_pipeline(tmp_path / "runs", NullSupervisor())


def test_reflex_supervisor_recording_pipeline_with_fixed_plan(tmp_path):
    run_pipeline(tmp_path / "runs", FixedPlanSupervisor())
