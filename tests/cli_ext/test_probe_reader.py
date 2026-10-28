from __future__ import annotations

import json

import numpy as np
from PIL import Image

from aether.cli_ext import main


def test_probe_reader_uses_synthetic_image_and_roi(tmp_path, capsys) -> None:
    # Synthetic RGB fixture generated here; it is not a screen capture.
    image = np.zeros((20, 100, 3), dtype=np.uint8)
    image[:, :50] = (200, 200, 200)
    path = tmp_path / "synthetic.png"
    Image.fromarray(image).save(path)
    assert main(["probe-reader", str(path), "--roi", "0,0,1,1", "--reader", "bar", "--rgb", "200,200,200"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["value"] == 0.5
