from __future__ import annotations

import json
import time

from aether.bench import verify_run
from aether.perception.frame_buffer import FrameBuffer
from aether.perception.pipeline import PerceptionPipeline
from aether.recording.session import RecordingSession
from aether.runtime.events import EventBus
from aether.runtime.identity import RunIdentity
from aether.sim.source import SyntheticSource
from prrex.backends.base import NullReflex, NullSupervisor, Subgoal, SupervisorOutput
from prrex.runtime import ReflexLoop, SupervisorLoop
from prrex.supervisor.planner import Planner


class FakeGovernorClient:
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
        return SupervisorOutput("synthetic-phase", "synthetic-objective", [Subgoal("hold synthetic objective")],
                                "fixed synthetic plan", 1.0, 0.0, self.name)


def run_pipeline(tmp_path, supervisor_backend):
    bus, buffer = EventBus(), FrameBuffer(512)
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
    run = recording.dir
    verified = verify_run(run, tmp_path / "verification")
    assert verified["status"] == "VERIFIED", verified
    assert client.calls > 0
    for stream in ("intended", "commanded", "delivered", "observed"):
        assert (run / "streams" / f"{stream}.jsonl").stat().st_size > 0
    index = [json.loads(line) for line in (run / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    disk = {int(path.stem) for path in (run / "frames").glob("*.jpg")}
    assert {row["seq"] for row in index} == disk
    return run


def test_reflex_supervisor_recording_pipeline_with_null_supervisor(tmp_path):
    run_pipeline(tmp_path / "runs", NullSupervisor())


def test_reflex_supervisor_recording_pipeline_with_fixed_plan(tmp_path):
    run_pipeline(tmp_path / "runs", FixedPlanSupervisor())
