from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from prrex.backends.nitrogen_reflex import build_request

FIXTURES = Path(__file__).parent / "fixtures"


def test_nitrogen_request_matches_primary_source_fixture():
    fixture = json.loads((FIXTURES / "nitrogen_request.json").read_text(encoding="utf-8"))
    request = build_request(np.zeros((256, 256, 3), dtype=np.uint8))
    assert request["type"] == fixture["_verified_fields"]["type"]
    assert request["image"].shape == (256, 256, 3)
    assert request["image"].dtype == np.uint8
    assert not fixture["unverified"]
