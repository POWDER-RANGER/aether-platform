from __future__ import annotations

import json

from scripts.soak.run_session import _has_stall_event


def test_stall_event_detection_uses_recorded_events(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps({"topic": "ordinary"}) + "\n", encoding="utf-8")
    assert _has_stall_event(path) is False
    path.write_text(json.dumps({"topic": "recovery.stall", "frame_seq": 5}) + "\n", encoding="utf-8")
    assert _has_stall_event(path) is True


def test_missing_or_invalid_events_do_not_claim_stall(tmp_path) -> None:
    assert _has_stall_event(tmp_path / "missing.jsonl") is False
    path = tmp_path / "events.jsonl"
    path.write_text("{broken\n", encoding="utf-8")
    assert _has_stall_event(path) is False
