"""Event bus: typed and versioned events, persistence before delivery, isolation of subscriber failures, redaction."""

import json

import pytest

from aether.control.intent_log import IntentLog, verify_log
from aether.runtime import EVENT_TYPES, EventBus, read_events
from aether.runtime.events import REDACTED, SCHEMA


def bus(tmp_path):
    store = IntentLog(tmp_path / "events.jsonl")
    return EventBus("s1", store), store


def test_event_has_identity_time_session_and_schema(tmp_path):
    b, _ = bus(tmp_path)
    e1 = b.publish("governor.halt", "test", {"reason": "x"}, correlation_id="task-1")
    e2 = b.publish("governor.halt", "test", {"reason": "y"}, causation_id=e1.id)
    assert e1.id != e2.id and len(e1.id) == 32
    assert e1.schema == SCHEMA == "aether.event/1" and e1.session_id == "s1"
    assert e1.correlation_id == "task-1" and e2.causation_id == e1.id
    assert e1.ts_mono <= e2.ts_mono and e1.ts_wall.endswith("+00:00")


@pytest.mark.parametrize(
    "etype,data,match",
    [
        ("no.such.type", {}, "unknown event type"),
        ("governor.halt", {}, "missing fields"),
        ("governor.halt", {"reason": float("nan")}, "not plain JSON"),
        ("governor.halt", {"reason": object()}, "not plain JSON"),
    ],
)
def test_invalid_events_are_refused_and_not_persisted(tmp_path, etype, data, match):
    b, store = bus(tmp_path)
    with pytest.raises(ValueError, match=match):
        b.publish(etype, "test", data)
    assert store.count == 0 and b.stats["published"] == 0


def test_events_are_persisted_hash_chained_before_delivery(tmp_path):
    b, store = bus(tmp_path)
    seen_on_disk = []
    b.subscribe(lambda e: seen_on_disk.append(store.count))
    b.publish("governor.halt", "test", {"reason": "x"})
    assert seen_on_disk == [1]  # already written when the subscriber ran
    store.close()
    ok, n, _, problem = verify_log(store.path)
    assert ok and n == 1, problem
    assert read_events(store.path)[0]["data"] == {"reason": "x"}


def test_failing_subscriber_does_not_break_publishing_or_other_subscribers(tmp_path):
    b, _ = bus(tmp_path)
    got = []

    def broken(e):
        raise RuntimeError("boom")

    b.subscribe(broken)
    b.subscribe(lambda e: got.append(e.type))
    b.publish("governor.halt", "test", {"reason": "x"})
    assert "governor.halt" in got
    assert b.stats["subscriber_errors"] >= 1
    assert b.events("bus.subscriber_error")[0].data["event_type"] == "governor.halt"


def test_secret_looking_fields_are_redacted_at_any_depth(tmp_path):
    b, store = bus(tmp_path)
    b.publish(
        "governor.record",
        "test",
        {
            "kind": "x",
            "session_key": "SECRET-VALUE-1",
            "nested": {"api_token": "SECRET-VALUE-2", "keys": ["K"], "bindings": ["W"]},
        },
    )
    store.close()
    raw = store.path.read_text(encoding="utf-8")
    assert "SECRET-VALUE" not in raw  # non-hex marker: cannot occur by chance in hashes or ids
    data = read_events(store.path)[0]["data"]
    assert data["session_key"] == REDACTED and data["nested"]["api_token"] == REDACTED
    assert data["nested"]["keys"] == REDACTED  # conservative: plural secret names are redacted too
    assert data["nested"]["bindings"] == ["W"]  # ordinary fields pass through


def test_subscribe_rejects_unknown_types_and_filters(tmp_path):
    b, _ = bus(tmp_path)
    with pytest.raises(ValueError):
        b.subscribe(lambda e: None, {"nope"})
    got = []
    b.subscribe(lambda e: got.append(e.type), {"governor.resume"})
    b.publish("governor.halt", "test", {"reason": "x"})
    b.publish("governor.resume", "test", {"how": "test"})
    assert got == ["governor.resume"]


def test_every_event_type_has_required_fields_declared():
    assert all(isinstance(v, frozenset) for v in EVENT_TYPES.values())
    assert json.dumps(sorted(EVENT_TYPES))  # names are plain strings
