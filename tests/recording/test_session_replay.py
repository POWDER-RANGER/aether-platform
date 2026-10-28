from __future__ import annotations

import json

import numpy as np
import pytest

from aether.recording.replay import list_runs, merged, summarize
from aether.recording.session import RecordingSession
from aether.runtime.events import EventBus
from aether.runtime.identity import RunIdentity


def test_recording_layout_manifest_sampling_and_stop(tmp_path) -> None:
    bus = EventBus()
    session = RecordingSession(tmp_path, RunIdentity(run_id="synthetic-run"), bus, frame_every_n=2)
    session.start()
    session.record("intended", 1.0, action="synthetic")
    with pytest.raises(ValueError, match="unknown stream"):
        session.record("unknown", 1.1)
    # Synthetic test images are generated here; they are not captured gameplay.
    synthetic = np.zeros((12, 16, 3), dtype=np.uint8)
    session.frame(1.0, synthetic)
    session.frame(2.0, synthetic)
    session.frame(3.0, synthetic)
    session.frame(4.0, synthetic)
    session.stop()

    run = tmp_path / "synthetic-run"
    assert (run / "manifest.json").is_file()
    assert (run / "events.jsonl").is_file()
    assert (run / "streams" / "intended.jsonl").is_file()
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["started"] is not None
    assert manifest["stopped"] is not None
    assert len(list((run / "frames").glob("*.jpg"))) == 2
    assert len((run / "frames.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_replay_merged_orders_records_across_streams_and_frames(tmp_path) -> None:
    run = tmp_path / "run"
    (run / "streams").mkdir(parents=True)
    (run / "streams" / "intended.jsonl").write_text('{"t_mono":3,"kind":"intent"}\n', encoding="utf-8")
    (run / "streams" / "observed.jsonl").write_text('{"t_mono":1,"kind":"observed"}\n', encoding="utf-8")
    (run / "frames.jsonl").write_text('{"t_mono":2,"seq":1}\n', encoding="utf-8")
    rows = list(merged(run))
    assert [row[0] for row in rows] == [1, 2, 3]
    assert [row[1] for row in rows] == ["observed", "frame", "intended"]


def test_list_runs_and_summarize_synthetic_run(tmp_path) -> None:
    run = tmp_path / "synthetic"
    (run / "streams").mkdir(parents=True)
    (run / "manifest.json").write_text(
        json.dumps({"identity": {"run_id": "synthetic"}, "streams": ["intended"]}), encoding="utf-8"
    )
    (run / "streams" / "intended.jsonl").write_text(
        '{"t_mono":10,"action":"synthetic"}\n{"t_mono":12,"action":"synthetic"}\n', encoding="utf-8"
    )
    listed = list_runs(tmp_path)
    assert listed[0]["identity"]["run_id"] == "synthetic"
    summary = summarize(run)
    assert summary["counts"]["intended"] == 2
    assert summary["duration_s"] == 2
