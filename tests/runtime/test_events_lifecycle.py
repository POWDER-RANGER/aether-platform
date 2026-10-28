from __future__ import annotations

import json
import queue
import time

import pytest

from aether.runtime.events import EventBus, JsonlSink
from aether.runtime.lifecycle import Component, Runtime, State, ThreadedComponent


def test_event_topics_sequence_and_wildcards() -> None:
    bus = EventBus()
    exact = bus.subscribe("x.y")
    prefix = bus.subscribe("x.*")
    all_topics = bus.subscribe("*")
    bus.publish("x.y", value=1)
    bus.publish("x.z", value=2)
    bus.publish("other", value=3)
    assert exact.q.qsize() == 1
    assert prefix.q.qsize() == 2
    assert all_topics.q.qsize() == 3
    assert [all_topics.q.get_nowait()["seq"] for _ in range(3)] == [1, 2, 3]


def test_subscriber_overflow_drops_oldest() -> None:
    bus = EventBus()
    sub = bus.subscribe("*")
    sub.q = queue.Queue(maxsize=2)
    bus.publish("a", value=1)
    bus.publish("a", value=2)
    bus.publish("a", value=3)
    assert sub.dropped == 1
    assert [sub.q.get_nowait()["value"], sub.q.get_nowait()["value"]] == [2, 3]


def test_publish_does_not_wait_for_subscriber() -> None:
    bus = EventBus()
    sub = bus.subscribe("*")
    sub.q = queue.Queue(maxsize=1)
    bus.publish("a")
    started = time.monotonic()
    for _ in range(1000):
        bus.publish("a")
    assert time.monotonic() - started < 1.0


def test_jsonl_sink_writes_and_joins(tmp_path) -> None:
    bus = EventBus()
    path = tmp_path / "nested" / "events.jsonl"
    sink = JsonlSink(bus, path, "*")
    sink.start()
    bus.publish("test.event", answer=42)
    sink.stop()
    assert not sink.is_alive()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert any(row["topic"] == "test.event" and row["answer"] == 42 for row in rows)


class RecordingComponent(Component):
    def __init__(self, bus, name, order, fail=False):
        super().__init__(bus)
        self.name = name
        self.order = order
        self.fail = fail

    def start(self):
        self.order.append("start:" + self.name)
        if self.fail:
            raise RuntimeError("start failure")

    def stop(self):
        self.order.append("stop:" + self.name)


def test_runtime_start_order_reverse_stop_and_lifecycle_events() -> None:
    bus = EventBus()
    events = bus.subscribe("lifecycle")
    order = []
    rt = Runtime(bus)
    rt.add(RecordingComponent(bus, "one", order))
    rt.add(RecordingComponent(bus, "two", order))
    rt.start()
    rt.stop()
    assert order == ["start:one", "start:two", "stop:two", "stop:one"]
    states = [events.q.get_nowait()["state"] for _ in range(events.q.qsize())]
    assert "starting" in states and "running" in states and "stopped" in states


def test_start_failure_marks_failed_and_stops_started_components() -> None:
    bus = EventBus()
    order = []
    rt = Runtime(bus)
    first = RecordingComponent(bus, "one", order)
    failing = RecordingComponent(bus, "two", order, fail=True)
    rt.add(first)
    rt.add(failing)
    with pytest.raises(RuntimeError, match="start failure"):
        rt.start()
    assert first.state is State.STOPPED
    assert failing.state is State.FAILED
    assert "stop:one" in order


def test_threaded_component_loop_exception_is_recorded() -> None:
    class Broken(ThreadedComponent):
        name = "broken"

        def loop_once(self):
            raise ValueError("loop failure")

    component = Broken(EventBus())
    component.start()
    deadline = time.monotonic() + 1
    while component.state is not State.FAILED and time.monotonic() < deadline:
        time.sleep(0.01)
    component.stop()
    assert component.state is State.FAILED
    assert "loop failure" in (component.error or "")
