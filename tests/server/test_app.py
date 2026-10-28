from __future__ import annotations

import http.client
import json
import threading
import time

from aether.evaluation.scorecard import Ledger
from aether.runtime.lifecycle import Runtime
from aether.runtime.topics import TopicBus
from aether.server.app import CommandCenter


def test_command_center_get_routes_and_read_only_surface(tmp_path) -> None:
    bus = TopicBus()
    cc = CommandCenter(bus, Runtime(bus), tmp_path / "runs", Ledger(tmp_path / "scorecard.jsonl"), port=0)
    thread = threading.Thread(target=cc.serve_forever, daemon=True)
    thread.start()
    deadline = time.monotonic() + 2
    while cc._srv is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert cc._srv is not None
    port = cc._srv.server_address[1]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        for path in ("/api/health", "/api/runs", "/api/scorecard", "/api/events"):
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
            assert response.status == 200
            assert isinstance(json.loads(body), (dict, list))

        connection.request("GET", "/design/../secret")
        response = connection.getresponse()
        response.read()
        assert response.status in (403, 404)

        connection.request("GET", "/api/runs/..")
        response = connection.getresponse()
        response.read()
        assert response.status in (403, 404)

        connection.request("POST", "/api/health")
        response = connection.getresponse()
        response.read()
        assert response.status == 501
        connection.request("PUT", "/api/health")
        response = connection.getresponse()
        response.read()
        assert response.status == 501
    finally:
        connection.close()
        cc.shutdown()
        thread.join(timeout=2)
