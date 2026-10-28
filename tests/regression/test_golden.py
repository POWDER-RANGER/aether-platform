import json
from pathlib import Path

from scripts.regression.update_golden import generate


def test_synthetic_golden_is_stable():
    expected = json.loads((Path(__file__).parent / "golden/scene.json").read_text(encoding="utf-8"))
    assert generate() == expected
