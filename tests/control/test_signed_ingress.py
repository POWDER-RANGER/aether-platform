"""Signed ingress end to end: GovernorClient -> local ZMQ -> Governor.handle_raw -> policy -> output adapter.

Review finding PR #2 #1. Uses the real transport (PUSH/PULL over 127.0.0.1) and the real verification path.
"""

import threading
import time

import pytest
import zmq
from conftest import FakeClock

from aether.control.adapters import DryRunAdapter
from aether.control.client import GovernorClient
from aether.control.governor import Governor
from aether.control.intent import Delegation, GamepadFrame, Source
from aether.control.intent_log import IntentLog, verify_log
from aether.control.motor import MotorModel, MotorProfile
from aether.control.policy import GovernorConfig
from aether.control.safety import KillSwitch

KEY = b"k" * 32
WRONG_KEY = b"w" * 32
FAST = MotorProfile(reaction_min_ms=0, reaction_max_ms=1, tremor_amp=0, drift_sigma=0)
PUSH = GamepadFrame(lx=1.0, buttons=frozenset({"SOUTH"}))


def _live(frames):
    return [f for f in frames if f != GamepadFrame.neutral()]


@pytest.fixture
def channel():
    """A PULL socket on a random localhost port, as the Governor binds it."""
    ctx = zmq.Context.instance()
    pull = ctx.socket(zmq.PULL)
    port = pull.bind_to_random_port("tcp://127.0.0.1")
    yield f"tcp://127.0.0.1:{port}", pull
    pull.close(0)


def _recv_all(pull, n, timeout_s=3.0):
    out, deadline = [], time.monotonic() + timeout_s
    while len(out) < n and time.monotonic() < deadline:
        if pull.poll(50):
            out.append(pull.recv())
    assert len(out) == n, f"received {len(out)} of {n} messages"
    return out


def _gov(tmp_path, clock):
    adapter = DryRunAdapter()
    log = IntentLog(tmp_path / "ingress.jsonl")
    gov = Governor(GovernorConfig(), MotorModel(FAST, seed=1), adapter, log, KillSwitch(tmp_path / "STOP"),
                   lambda: True, clock=clock, seal_key=KEY)  # fmt: skip
    return gov, adapter, log


def _ticks(gov, clock, n=30):
    for _ in range(n):
        clock.advance(1 / 120)
        gov.tick()


def test_signed_player_intent_over_zmq_reaches_output(tmp_path, channel):
    endpoint, pull = channel
    c = FakeClock()
    gov, adapter, log = _gov(tmp_path, c)
    client = GovernorClient(endpoint, KEY, Source.PLAYER, clock=c)
    client.send_frames([PUSH], frame_dt_ms=1000 / 120)
    for raw in _recv_all(pull, 1):
        gov.handle_raw(KEY, raw)
    _ticks(gov, c)
    client.close()
    assert gov.stats["allowed"] == 1 and gov.stats["bad_signature"] == 0
    assert adapter.frames[-1].lx > 0.9 and "SOUTH" in adapter.frames[-1].buttons


def test_signed_companion_intent_needs_a_delegation(tmp_path, channel):
    endpoint, pull = channel
    c = FakeClock()
    gov, adapter, _ = _gov(tmp_path, c)
    client = GovernorClient(endpoint, KEY, Source.REFLEX, clock=c)
    client.send_frames([PUSH], frame_dt_ms=1000 / 120, delegation_id="d1")  # no grant yet
    for raw in _recv_all(pull, 1):
        gov.handle_raw(KEY, raw)
    _ticks(gov, c)
    assert gov.stats["denied"] == 1 and not _live(adapter.frames)

    client.grant(Delegation(id="d1", scope="full_autopilot", granted_at=c()))
    client.send_frames([PUSH], frame_dt_ms=1000 / 120, delegation_id="d1")
    for raw in _recv_all(pull, 2):
        gov.handle_raw(KEY, raw)
    _ticks(gov, c)
    client.close()
    assert gov.stats["allowed"] == 1
    assert adapter.frames[-1].lx > 0.9


def test_wrong_key_and_tampered_messages_are_rejected_without_output(tmp_path, channel):
    endpoint, pull = channel
    c = FakeClock()
    gov, adapter, log = _gov(tmp_path, c)
    forger = GovernorClient(endpoint, WRONG_KEY, Source.PLAYER, clock=c)
    forger.send_frames([PUSH], frame_dt_ms=1000 / 120)
    forger.halt("forged halt must not be honoured either")
    forged_intent, forged_halt = _recv_all(pull, 2)  # one sender: order is preserved
    honest = GovernorClient(endpoint, KEY, Source.PLAYER, clock=c)
    honest.send_frames([PUSH], frame_dt_ms=1000 / 120)
    (good,) = _recv_all(pull, 1)  # received separately: two PUSH sockets have no mutual ordering
    tampered = good.replace(b'"lx": 1.0', b'"lx": -1.0') if b'"lx": 1.0' in good else good[:-2] + b"xx"
    assert tampered != good
    for raw in (forged_intent, forged_halt, tampered):
        gov.handle_raw(KEY, raw)
    _ticks(gov, c)
    forger.close()
    honest.close()
    assert gov.stats["bad_signature"] == 3
    assert gov.stats["allowed"] == 0 and not gov.policy.halted
    assert not _live(adapter.frames)
    gov.close()
    ok, _, _, problem = verify_log(log.path)
    assert ok, problem
    assert log.path.read_text(encoding="utf-8").count("rejected_message") == 3


def test_serve_loop_end_to_end(tmp_path):
    """The real serve() loop on a localhost port: grant, companion intent, forged intent, shutdown."""
    ctx = zmq.Context.instance()
    probe = ctx.socket(zmq.PULL)
    port = probe.bind_to_random_port("tcp://127.0.0.1")
    probe.close(0)
    endpoint = f"tcp://127.0.0.1:{port}"
    adapter = DryRunAdapter()
    log = IntentLog(tmp_path / "serve.jsonl")
    gov = Governor(GovernorConfig(), MotorModel(FAST, seed=1), adapter, log, KillSwitch(tmp_path / "STOP"),
                   lambda: True, seal_key=KEY)  # fmt: skip
    t = threading.Thread(target=gov.serve, args=(endpoint, KEY), kwargs={"tick_hz": 120.0}, daemon=True)
    t.start()
    time.sleep(0.2)
    forger = GovernorClient(endpoint, WRONG_KEY, Source.REFLEX)
    client = GovernorClient(endpoint, KEY, Source.REFLEX)
    forger.send_frames([GamepadFrame(ry=-1.0)], frame_dt_ms=1000 / 120, delegation_id="d1")
    client.grant(Delegation(id="d1", scope="full_autopilot", granted_at=time.monotonic()))
    time.sleep(0.05)
    client.send_frames([PUSH] * 12, frame_dt_ms=1000 / 120, delegation_id="d1")
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and not any(f.lx > 0.9 for f in adapter.frames):
        time.sleep(0.02)
    client.shutdown()
    t.join(timeout=3.0)
    forger.close()
    client.close()
    assert not t.is_alive(), "serve() did not stop on a signed shutdown"
    assert any(f.lx > 0.9 and "SOUTH" in f.buttons for f in adapter.frames)
    assert not any(f.ry < -0.5 for f in adapter.frames), "forged frames reached the controller"
    assert gov.stats["bad_signature"] == 1 and gov.stats["allowed"] >= 1
    assert adapter.frames[-1] == GamepadFrame.neutral()  # close() leaves the pad neutral
