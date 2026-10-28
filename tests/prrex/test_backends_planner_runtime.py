from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from aether.perception.frame_buffer import Frame, FrameBuffer
from aether.perception.pipeline import PerceptionPipeline
from aether.perception.world_state import Fact, WorldState
from aether.runtime.events import EventBus
from prrex.backends.base import (
    NullReflex,
    NullSupervisor,
    Subgoal,
    SupervisorOutput,
    make_reflex,
    make_supervisor,
)
from prrex.runtime import ReflexLoop, SupervisorLoop
from prrex.supervisor.planner import Planner, eval_check
from prrex.supervisor.recovery import StallDetector


def test_registry_null_backends_and_outputs() -> None:
    assert isinstance(make_reflex("null"), NullReflex)
    assert isinstance(make_supervisor("null"), NullSupervisor)
    reflex = NullReflex().act(np.zeros((256, 256, 3), dtype=np.uint8), None, 4)
    assert len(reflex.frames) == 4
    assert reflex.confidence == 0
    assert reflex.meta["null"] is True
    supervisor = NullSupervisor().assess({}, "", None, [])
    assert supervisor.confidence == 0
    assert supervisor.subgoals == []


@pytest.mark.parametrize(
    ("value", "check", "expected"),
    [
        (3, "score == 3", True),
        (3, "score != 4", True),
        (3, "score < 4", True),
        (3, "score > 2", True),
        (3, "score <= 3", True),
        (3, "score >= 3", True),
        (True, "ready == True", True),
        (False, "ready != True", True),
    ],
)
def test_eval_check_operators_and_literals(value, check, expected) -> None:
    key = check.split()[0]
    state = WorldState()
    state.set(key, Fact(value, 1.0, 1.0, "synthetic"))
    assert eval_check(check, state) is expected


def test_eval_check_missing_and_type_mismatch_return_none() -> None:
    state = WorldState()
    state.set("text", Fact("ready", 1.0, 1.0, "synthetic"))
    state.set("flag", Fact(True, 1.0, 1.0, "synthetic"))
    assert eval_check("missing == 1", state) is None
    assert eval_check("text > 1", state) is None
    assert eval_check("flag < 2", state) is None


def test_planner_rejects_low_confidence_and_empty_plan_then_advances() -> None:
    planner = Planner(min_confidence=0.5)
    assert not planner.apply(SupervisorOutput(None, None, [Subgoal("x")], "", 0.1, 0, "test"))
    assert not planner.apply(SupervisorOutput(None, None, [], "", 1.0, 0, "test"))
    assert planner.apply(SupervisorOutput(None, "goal", [Subgoal("first"), Subgoal("second")], "", 0.9, 0, "test"))
    assert planner.s.active.text == "first"
    assert planner.step(WorldState()) == "first"


def test_planner_success_and_timeout_use_injected_clock() -> None:
    now = [10.0]
    planner = Planner(clock=lambda: now[0])
    state = WorldState()
    state.set("done", Fact(True, 1.0, 10.0, "synthetic"))
    assert planner.apply(SupervisorOutput(None, None, [Subgoal("one", "done == True"), Subgoal("two")], "", 1, 0, "test"))
    assert planner.step(state) == "two"
    now[0] = 20.0
    timed = Planner(clock=lambda: now[0])
    assert timed.apply(SupervisorOutput(None, None, [Subgoal("short", timeout_s=1)], "", 1, 0, "test"))
    now[0] = 22.0
    timed.step(WorldState())
    assert timed.s.replan_requested is True


def test_stall_detector_motion_and_no_motion_cases() -> None:
    detector = StallDetector(window_s=10)
    # Synthetic images only: changing pixels must not be classified as a stall.
    for index in range(8):
        image = np.full((16, 16, 3), index * 20, dtype=np.uint8)
        assert detector.update(Frame(index + 1, float(index), image, "synthetic"), True) is False

    stalled = StallDetector(window_s=10)
    still = np.zeros((16, 16, 3), dtype=np.uint8)
    result = False
    for index in range(8):
        result = stalled.update(Frame(index + 1, float(index), still.copy(), "synthetic"), True)
    assert result is True

    idle = StallDetector(window_s=10)
    result = False
    for index in range(8):
        result = idle.update(Frame(index + 1, float(index), still.copy(), "synthetic"), False)
    assert result is False


class FakeGovernor:
    def __init__(self):
        self.calls = []

    def send_frames(self, frames, **kwargs):
        self.calls.append((frames, kwargs))


def test_reflex_loop_sends_ceil_horizon_and_publishes_event() -> None:
    bus = EventBus()
    events = bus.subscribe("reflex.chunk")
    buf = FrameBuffer()
    # Synthetic image; no screen capture is involved in this unit test.
    buf.push(1.0, np.zeros((32, 32, 3), dtype=np.uint8), source="synthetic")
    governor = FakeGovernor()
    perception = PerceptionPipeline(bus, {}, {})
    loop = ReflexLoop(bus, buf, NullReflex(), governor, Planner(), perception, None, 16, 0.26)
    loop.loop_once()
    frames, kwargs = governor.calls[0]
    assert len(frames) == 5
    assert kwargs["frame_dt_ms"] == pytest.approx(1000 / 120)
    assert kwargs["ttl_ms"] == 400
    assert events.q.get_nowait()["topic"] == "reflex.chunk"


def test_supervisor_loop_does_nothing_when_plan_is_active() -> None:
    class NeverCall:
        def assess(self, *args):
            raise AssertionError("active plan must not trigger supervisor")

    bus = EventBus()
    buf = FrameBuffer()
    buf.push(1.0, np.zeros((8, 8, 3), dtype=np.uint8), source="synthetic")
    planner = Planner()
    planner.apply(SupervisorOutput(None, "goal", [Subgoal("active")], "", 1.0, 0, "test"))
    perception = PerceptionPipeline(bus, {}, {})
    loop = SupervisorLoop(bus, buf, NeverCall(), planner, perception, {}, None)
    loop.loop_once()
    assert planner.s.active.text == "active"


def test_ollama_supervisor_parses_json_and_degrades_on_malformed(monkeypatch) -> None:
    from prrex.backends import ollama_vlm

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"message": {"content": self.body}}).encode()

    monkeypatch.setattr(ollama_vlm.urllib.request, "urlopen", lambda *a, **k: Response(
        json.dumps({"phase": "gameplay", "objective": "synthetic", "subgoals": [{"text": "observe"}],
                    "explanation": "parsed", "confidence": 0.8})
    ))
    good = ollama_vlm.OllamaSupervisor().assess({}, "", None, [])
    assert good.confidence == 0.8
    assert good.subgoals[0].text == "observe"

    monkeypatch.setattr(ollama_vlm.urllib.request, "urlopen", lambda *a, **k: Response("not-json"))
    bad = ollama_vlm.OllamaSupervisor().assess({}, "", None, [])
    assert bad.confidence == 0
    assert bad.subgoals == []
    assert "unparseable" in bad.explanation


def test_nitrogen_reflex_constructs_with_fake_zmq_socket(monkeypatch) -> None:
    pytest.importorskip("zmq")
    from prrex.backends import nitrogen_reflex

    class FakeSocket:
        def __init__(self):
            self.options = []
            self.endpoint = None

        def setsockopt(self, key, value):
            self.options.append((key, value))

        def connect(self, endpoint):
            self.endpoint = endpoint

    socket = FakeSocket()
    context = SimpleNamespace(socket=lambda _kind: socket)
    fake_zmq = SimpleNamespace(
        Context=SimpleNamespace(instance=lambda: context),
        REQ=1,
        RCVTIMEO=2,
        LINGER=3,
    )
    monkeypatch.setitem(sys.modules, "zmq", fake_zmq)
    adapter = nitrogen_reflex.NitrogenReflex()
    assert adapter.sock is socket
    assert socket.endpoint == "tcp://127.0.0.1:5555"
