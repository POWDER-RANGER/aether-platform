import json

import pytest

from aether.calibration.labels import append_label, score_labels


def test_label_store_and_score(tmp_path):
    path = tmp_path / "labels.jsonl"
    row = append_label(path, run_id="synthetic", frame_seq=1, roi="health", true_value=0.8, labeller="owner")
    assert json.loads(path.read_text(encoding="utf-8").strip()) == row
    result = score_labels([row, {**row, "true_value": 0.4}], [0.7, 0.5], "bar")
    assert result["value"] == pytest.approx(0.1)
    assert score_labels([{"true_value": "yes"}], ["yes"], "ocr")["value"] == 1.0
    assert score_labels([], [], "template")["value"] is None
