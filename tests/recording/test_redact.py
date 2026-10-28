import json

import numpy as np
import pytest
from PIL import Image

from aether.recording.redact import assert_shareable, redact_run


def test_redact_copy_and_gate(tmp_path):
    source = tmp_path / "src"
    (source / "frames").mkdir(parents=True)
    Image.fromarray(np.full((20, 20, 3), 255, dtype=np.uint8)).save(source / "frames/00000001.jpg", quality=100)
    (source / "manifest.json").write_text(json.dumps({"identity": {"run_id": "r1"}}))
    output = redact_run(source, tmp_path / "out", [(0.25, 0.25, 0.75, 0.75)])
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["redaction"]["source_run_id"] == "r1"
    assert manifest["redaction"]["frame_pixels_blacked"] is True
    assert_shareable(output, True)
    with Image.open(output / "frames/00000001.jpg") as image:
        assert image.getpixel((10, 10)) == (0, 0, 0)
    with pytest.raises(ValueError, match="unredacted"):
        assert_shareable(source, True)


def test_empty_redaction_rejected(tmp_path):
    source = tmp_path / "src"
    (source / "frames").mkdir(parents=True)
    (source / "manifest.json").write_text(json.dumps({"identity": {"run_id": "r1"}}))
    with pytest.raises(ValueError, match="no redaction boxes"):
        redact_run(source, tmp_path / "out", [])
    assert not (tmp_path / "out").exists()


def test_manifest_with_no_boxes_not_shareable(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    manifest = {"redaction": {"redacted": True, "frame_pixels_blacked": True, "boxes_normalized": []}}
    (run / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unredacted"):
        assert_shareable(run, True)
