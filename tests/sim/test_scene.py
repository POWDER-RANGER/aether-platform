from __future__ import annotations

import time

import numpy as np

from aether.bench import verify_run
from aether.perception.frame_buffer import FrameBuffer
from aether.perception.preprocess import roi_crop
from aether.perception.readers import BarReader
from aether.recording.session import RecordingSession
from aether.runtime.events import EventBus
from aether.runtime.identity import RunIdentity
from aether.sim.scene import SyntheticScene
from aether.sim.source import SyntheticSource


def test_scene_is_deterministic_and_health_schedule_is_readable():
    a, b = SyntheticScene(seed=11), SyntheticScene(seed=11)
    for seq in range(1, 20):
        frame = a.frame(seq, seq / 10)
        assert np.array_equal(frame, b.frame(seq, seq / 10))
        crop = roi_crop(frame, (12/320, 12/180, 112/320, 22/180))
        fact = BarReader("health", (40, 220, 80), tol=8, min_conf_pixels=1).read(crop, seq / 10, seq)
        assert fact is not None
        assert abs(float(fact.value) - a.health_ratio(seq / 10)) <= 0.05


def test_synthetic_source_records_frames_and_streams(tmp_path):
    bus, buffer = EventBus(), FrameBuffer(512)
    source = SyntheticSource(bus, buffer, fps=20, seed=3)
    identity = RunIdentity(run_id="synthetic-e2e")
    rec = RecordingSession(tmp_path / "runs", identity, bus, frame_every_n=1)
    rec.start()
    source.start()
    deadline = time.monotonic() + 3
    last_seq = 0
    try:
        while time.monotonic() < deadline:
            frame = buffer.wait_newer(last_seq, 0.2)
            if frame:
                last_seq = frame.seq
                rec.record("intended", frame.t_mono, source="synthetic", seq=frame.seq)
                rec.record("commanded", frame.t_mono, source="synthetic", seq=frame.seq)
                rec.record("delivered", frame.t_mono, source="synthetic", seq=frame.seq)
                rec.record("observed", frame.t_mono, source="synthetic", seq=frame.seq)
                rec.frame(frame.t_mono, frame.image)
    finally:
        source.stop()
        rec.stop()
    run = tmp_path / "runs" / "synthetic-e2e"
    result = verify_run(run, tmp_path / "evidence")
    assert result["status"] == "VERIFIED"
    assert last_seq > 0
    assert all((run / "streams" / f"{name}.jsonl").stat().st_size > 0 for name in ("intended", "commanded", "delivered", "observed"))
    rows = [__import__("json").loads(line) for line in (run / "frames.jsonl").read_text().splitlines()]
    assert {row["seq"] for row in rows} == {int(path.stem) for path in (run / "frames").glob("*.jpg")}
