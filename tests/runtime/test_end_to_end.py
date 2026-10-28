"""Runtime slice 1 end to end: register an agent, discover it, assign a task, submit a signed intent, get a
Governor decision, execute the authorized action, record the event sequence, and produce verifiable evidence."""

import time

import zmq
from conftest import KEY

from aether.control.adapters import DryRunAdapter
from aether.control.client import GovernorClient
from aether.control.governor import Governor
from aether.control.intent import Delegation, GamepadFrame, Source
from aether.control.intent_log import IntentLog
from aether.control.motor import MotorModel, MotorProfile
from aether.control.policy import GovernorConfig
from aether.control.safety import KillSwitch
from aether.control.settings import Settings
from aether.runtime import AgentState, Runtime, TaskState, read_events

SESSION_KEY = b"k" * 32
FAST = MotorProfile(reaction_min_ms=0, reaction_max_ms=1, tremor_amp=0, drift_sigma=0)
PUSH = GamepadFrame(lx=1.0, buttons=frozenset({"SOUTH"}))


def _recv(pull, n, timeout_s=3.0):
    out, end = [], time.monotonic() + timeout_s
    while len(out) < n and time.monotonic() < end:
        if pull.poll(50):
            out.append(pull.recv())
    assert len(out) == n
    return out


def test_agent_task_intent_decision_action_events_evidence(tmp_path):
    rt = Runtime(Settings(), tmp_path, KEY, session_id="s-e2e")
    pull = zmq.Context.instance().socket(zmq.PULL)
    endpoint = f"tcp://127.0.0.1:{pull.bind_to_random_port('tcp://127.0.0.1')}"

    # Governor, observed by the runtime (read-only)
    glog = IntentLog(tmp_path / "governor.jsonl")
    rt.observe_governor(glog)
    sink = DryRunAdapter()
    gov = Governor(GovernorConfig(), MotorModel(FAST, seed=1), rt.observe_adapter(sink), glog,
                   KillSwitch(tmp_path / "STOP"), lambda: True, seal_key=KEY)  # fmt: skip

    # 1. register an agent and discover it by capability
    agent = rt.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")
    rt.agents.transition(agent.agent_id, AgentState.READY, "initialized")
    found = rt.agents.discover("controller.propose")
    assert [a.agent_id for a in found] == [agent.agent_id]

    # 2. assign it a task; it takes the controller-output resource for the task's duration
    task = rt.tasks.create("drive", "controller.propose", timeout_s=30)
    rt.tasks.assign(task.task_id, agent.agent_id)
    rt.agents.transition(agent.agent_id, AgentState.RUNNING, "task started")
    rt.agents.claim(agent.agent_id, "controller.output")
    rt.tasks.start(task.task_id)

    # 3. the player grants a delegation; the agent submits signed intents through the real transport
    player = GovernorClient(endpoint, SESSION_KEY, Source.PLAYER)
    reflex = GovernorClient(endpoint, SESSION_KEY, Source.REFLEX)
    rt.correlate(reflex.producer, task.task_id)
    forger = GovernorClient(endpoint, b"x" * 32, Source.REFLEX)
    player.grant(Delegation(id="d1", scope="full_autopilot", granted_at=time.monotonic()))
    for raw in _recv(pull, 1):
        gov.handle_raw(SESSION_KEY, raw)
    reflex.send_frames([PUSH] * 8, frame_dt_ms=1000 / 120, delegation_id="d1")
    for raw in _recv(pull, 1):
        gov.handle_raw(SESSION_KEY, raw)
    forger.send_frames([GamepadFrame(ry=-1.0)], frame_dt_ms=1000 / 120, delegation_id="d1")
    for raw in _recv(pull, 1):
        gov.handle_raw(SESSION_KEY, raw)

    # 4. the Governor executes the authorized action
    for _ in range(80):  # the motor model moves the stick at human speed
        gov.tick()
        time.sleep(1 / 240)
    assert any(f.lx > 0.9 and "SOUTH" in f.buttons for f in sink.frames)
    assert not any(f.ry < -0.5 for f in sink.frames)

    # 5. finish: task done, agent stops (resource released), everything closed and sealed
    rt.tasks.complete(task.task_id, {"allowed": gov.stats["allowed"]})
    rt.agents.transition(agent.agent_id, AgentState.STOPPED, "task done")
    gov.close()
    for c in (player, reflex, forger):
        c.close()
    pull.close(0)
    rt.close()

    # 6. the event sequence, read back from disk
    events = read_events(rt.events_path)
    types = [e["type"] for e in events]
    expected_order = [
        "session.started", "governor.session", "agent.registered", "agent.state", "task.created", "task.assigned",
        "agent.state", "resource.claimed", "task.state", "governor.grant", "governor.decision", "governor.rejected",
        "adapter.active", "task.state", "agent.state", "resource.released", "governor.session", "session.ended",
    ]  # fmt: skip
    it = iter(types)
    assert all(t in it for t in expected_order), types  # in this order (other events may sit between)
    decision = next(e for e in events if e["type"] == "governor.decision")
    assert decision["data"]["allow"] is True and decision["correlation_id"] == task.task_id
    assert all(e["session_id"] == "s-e2e" and e["schema"] == "aether.event/1" for e in events)
    assert len({e["id"] for e in events}) == len(events)
    task_history = [e["type"] for e in events if e["correlation_id"] == task.task_id]
    assert task_history[:3] == ["task.created", "task.assigned", "task.state"] and "governor.decision" in task_history

    # 7. verifiable evidence: both logs chain- and seal-verified; no secrets in it
    receipt = rt.receipt()
    assert receipt["ok"], receipt
    assert [entry["chain_ok"] and entry["seal_ok"] for entry in receipt["logs"]] == [True, True]
    assert receipt["event_counts"]["governor.decision"] == 1 and receipt["event_counts"]["governor.rejected"] == 1
    assert SESSION_KEY.hex() not in rt.events_path.read_text(encoding="utf-8")
    assert task.state == TaskState.DONE and rt.agents.owner("controller.output") is None


def test_receipt_detects_a_tampered_event_log(tmp_path):
    rt = Runtime(Settings(), tmp_path, KEY, session_id="s-tamper")
    rt.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")
    rt.close()
    text = rt.events_path.read_text(encoding="utf-8")
    rt.events_path.write_text(text.replace("prrex.reflex", "prrex.forged"), encoding="utf-8")
    receipt = rt.receipt()
    assert not receipt["ok"] and "hash mismatch" in receipt["logs"][0]["problem"]
