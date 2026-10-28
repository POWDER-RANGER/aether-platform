from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image

from aether.bench import percentile, summarize_samples, verify_run, write_evidence


def test_percentiles_and_empty_samples() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5
    assert percentile([1.0, 2.0, 3.0, 4.0], 95) == pytest.approx(3.85)
    assert percentile([], 99) is None
    assert summarize_samples([])["count"] == 0
    with pytest.raises(ValueError):
        percentile([1.0], 101)


def test_write_evidence_uses_requested_directory(tmp_path) -> None:
    path = write_evidence("E-06", "synthetic-run", {"raw_samples": [1.0]}, tmp_path)
    assert path == tmp_path / "E-06" / "synthetic-run.json"
    assert json.loads(path.read_text(encoding="utf-8"))["raw_samples"] == [1.0]
    with pytest.raises(ValueError):
        write_evidence("../escape", "run", {}, tmp_path)


def make_synthetic_run(root):
    run = root / "synthetic-run"
    (run / "streams").mkdir(parents=True)
    (run / "frames").mkdir()
    (run / "manifest.json").write_text(json.dumps({"identity": {"run_id": "synthetic-run"}}), encoding="utf-8")
    (run / "streams" / "intended.jsonl").write_text(
        '{"t_mono":1.0,"kind":"synthetic"}\n{"t_mono":2.0,"kind":"synthetic"}\n', encoding="utf-8"
    )
    (run / "frames.jsonl").write_text('{"seq":1,"t_mono":1.5}\n', encoding="utf-8")
    (run / "events.jsonl").write_text('{"topic":"synthetic.event"}\n', encoding="utf-8")
    # Synthetic test fixture only; this is not a captured screen frame.
    synthetic_image = np.zeros((8, 8, 3), dtype=np.uint8)
    Image.fromarray(synthetic_image).save(run / "frames" / "00000001.jpg")
    return run


def test_verify_run_validates_manifest_streams_frames_and_events(tmp_path) -> None:
    run = make_synthetic_run(tmp_path)
    result = verify_run(run, tmp_path / "evidence")
    assert result["status"] == "VERIFIED"
    assert result["streams"]["intended"]["count"] == 2
    assert result["streams"]["intended"]["largest_gap_s"] == 1.0
    assert result["frames_match"] is True
    assert result["event_count"] == 1
    assert (tmp_path / "evidence" / "E-10" / "synthetic-run.json").is_file()


def test_verify_run_fails_nonmonotonic_stream_and_bad_events(tmp_path) -> None:
    run = make_synthetic_run(tmp_path)
    (run / "streams" / "intended.jsonl").write_text(
        '{"t_mono":2.0}\n{"t_mono":1.0}\n', encoding="utf-8"
    )
    (run / "events.jsonl").write_text("{bad json\n", encoding="utf-8")
    result = verify_run(run, tmp_path / "evidence")
    assert result["status"] == "FAILED"
    assert any("not monotonic" in failure for failure in result["failures"])
    assert any("events.jsonl invalid" in failure for failure in result["failures"])
