from __future__ import annotations

import http.client
import json
import threading
import time

import numpy as np
import pytest
from PIL import Image

from aether.evaluation.scorecard import Ledger
from aether.runtime.events import EventBus
from aether.runtime.lifecycle import Runtime
from aether.server.app import CommandCenter


def make_run(root):
    run = root / "run-1"
    (run / "streams").mkdir(parents=True)
    (run / "frames").mkdir()
    (run / "manifest.json").write_text(
        json.dumps({"identity": {"run_id": "run-1", "mode": "research"}, "streams": ["intended"]}),
        encoding="utf-8",
    )
    (run / "streams" / "intended.jsonl").write_text('{"t_mono":1.0,"action":"synthetic"}\n', encoding="utf-8")
    (run / "frames.jsonl").write_text('{"seq":1,"t_mono":1.0}\n', encoding="utf-8")
    (run / "events.jsonl").write_text('{"t_mono":1.0,"topic":"synthetic.event"}\n', encoding="utf-8")
    # Synthetic image fixture; not captured gameplay.
    Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8)).save(run / "frames" / "00000001.jpg")
    return run


def test_command_center_views_run_detail_replay_and_loopback(tmp_path) -> None:
    make_run(tmp_path / "runs")
    bus = EventBus()
    cc = CommandCenter(bus, Runtime(bus), tmp_path / "runs", Ledger(tmp_path / "scorecard.jsonl"), port=0)
    thread = threading.Thread(target=cc.serve_forever, daemon=True)
    thread.start()
    deadline = time.monotonic() + 2
    while cc._srv is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert cc._srv is not None
    connection = http.client.HTTPConnection("127.0.0.1", cc._srv.server_address[1], timeout=2)
    try:
        for path in ("/runs/run-1", "/replay/run-1", "/scorecard", "/overlay", "/calibrate"):
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
            assert response.status == 200
            assert b"<!doctype html>" in body.lower()

        connection.request("GET", "/api/runs/run-1")
        response = connection.getresponse()
        detail = json.loads(response.read())
        assert response.status == 200
        assert detail["manifest"]["identity"]["run_id"] == "run-1"
        assert detail["stream_counts"]["intended"] == 1

        connection.request("GET", "/api/runs/run-1/timeline")
        response = connection.getresponse()
        timeline = json.loads(response.read())
        assert response.status == 200
        assert {row["stream"] for row in timeline} >= {"intended", "frame", "event"}

        connection.request("GET", "/api/runs/run-1/frames/00000001.jpg")
        response = connection.getresponse()
        assert response.status == 200
        assert response.read().startswith(b"\xff\xd8")

        connection.request("GET", "/api/runs/..")
        response = connection.getresponse()
        response.read()
        assert response.status == 404
        connection.request("GET", "/runs/..")
        response = connection.getresponse()
        response.read()
        assert response.status == 404
    finally:
        connection.close()
        cc.shutdown()
        thread.join(timeout=2)


def test_command_center_refuses_non_loopback_bind(tmp_path) -> None:
    with pytest.raises(ValueError, match="127.0.0.1"):
        CommandCenter(EventBus(), None, tmp_path, Ledger(tmp_path / "scorecard.jsonl"), host="0.0.0.0")
