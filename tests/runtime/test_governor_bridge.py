"""Governor observation is observe-only: it reports decisions and failures but cannot change any outcome."""

import pytest
from conftest import KEY, FakeClock

from aether.control.adapters import DryRunAdapter, OutputAdapter
from aether.control.governor import Governor
from aether.control.intent import Delegation, GamepadFrame, IntentPacket, Source
from aether.control.intent_log import IntentLog
from aether.control.motor import MotorModel, MotorProfile
from aether.control.policy import GovernorConfig
from aether.control.safety import KillSwitch

FAST = MotorProfile(reaction_min_ms=0, reaction_max_ms=1, tremor_amp=0, drift_sigma=0)
PUSH = GamepadFrame(lx=1.0, buttons=frozenset({"SOUTH"}))


def run_scenario(tmp_path, name, attach=None, focused=lambda: True):
    """Grant, companion intent, undelegated intent, player override, focus loss, halt. Returns adapter frames."""
    c = FakeClock()
    log = IntentLog(tmp_path / f"{name}.jsonl")
    adapter = DryRunAdapter()
    out = attach(log, adapter) if attach else adapter
    kill = KillSwitch(tmp_path / f"{name}.STOP")
    focus = {"v": True}
    gov = Governor(
        GovernorConfig(), MotorModel(FAST, seed=1), out, log, kill, lambda: focus["v"], clock=c, seal_key=KEY
    )

    def send(seq, src, frame, deleg=None):
        gov.handle("intent", IntentPacket(seq=seq, source=src, created_at=c(), ttl_ms=250, frames=(frame,),
                                          delegation_id=deleg, producer=f"{src.value}-p").to_dict())  # fmt: skip

    def ticks(n):
        for _ in range(n):
            c.advance(1 / 120)
            gov.tick()

    send(1, Source.REFLEX, PUSH, "d1")  # no delegation yet: denied
    gov.handle("grant", Delegation(id="d1", scope="full_autopilot", granted_at=c()).to_dict())
    send(2, Source.REFLEX, PUSH, "d1")  # allowed
    ticks(20)
    send(3, Source.PLAYER, GamepadFrame(ly=1.0))  # player input pre-empts
    send(4, Source.REFLEX, PUSH, "d1")  # denied: player override
    ticks(200)
    focus["v"] = False
    send(5, Source.REFLEX, PUSH, "d1")  # denied: window not in front
    kill.trip("test halt")
    ticks(5)
    gov.close()
    return [f.to_dict() for f in adapter.frames], gov.stats, log


def test_observation_does_not_change_any_controller_output(tmp_path, runtime):
    plain, plain_stats, _ = run_scenario(tmp_path, "plain")

    def attach(log, adapter):
        runtime.observe_governor(log)
        return runtime.observe_adapter(adapter)

    observed, obs_stats, _ = run_scenario(tmp_path, "observed", attach)
    assert observed == plain and obs_stats == plain_stats


def test_decisions_overrides_focus_and_halt_are_reported(tmp_path, runtime):
    def attach(log, adapter):
        runtime.observe_governor(log)
        return runtime.observe_adapter(adapter)

    run_scenario(tmp_path, "observed", attach)
    decisions = runtime.bus.events("governor.decision")
    assert [d.data["allow"] for d in decisions] == [False, True, True, False, False]
    assert runtime.bus.events("governor.override")[0].data["seq"] == 4
    assert runtime.bus.events("governor.focus_block")[0].data["seq"] == 5
    assert runtime.bus.events("governor.halt")[0].data["reason"] == "test halt"
    assert runtime.bus.events("governor.grant")[0].data["refused"] == []
    assert [e.data["phase"] for e in runtime.bus.events("governor.session")] == ["start", "end"]
    assert runtime.bus.events("adapter.active") and runtime.bus.events("adapter.neutral")
    assert all(isinstance(d.data["intent_log_n"], int) for d in decisions)  # links back to the Governor's own record


def test_a_broken_event_pipeline_cannot_affect_the_governor(tmp_path, runtime):
    plain, plain_stats, _ = run_scenario(tmp_path, "plain")

    def attach(log, adapter):
        def explode(record):
            raise RuntimeError("observer failure")

        log.add_observer(explode)
        return adapter

    observed, obs_stats, log = run_scenario(tmp_path, "broken", attach)
    assert observed == plain and obs_stats == plain_stats
    assert log.observer_errors > 0


def test_observer_receives_a_copy_it_cannot_alter(tmp_path):
    log = IntentLog(tmp_path / "l.jsonl")
    log.add_observer(lambda r: r.update(kind="tampered"))
    log.append("grant", delegation={"id": "d1"})
    log.close()
    assert '"kind":"grant"' in log.path.read_text(encoding="utf-8")


def test_adapter_failure_is_reported_and_still_raised(runtime):
    class Broken(OutputAdapter):
        name = "broken"

        def apply(self, frame):
            raise OSError("device unplugged")

    ad = runtime.observe_adapter(Broken())
    with pytest.raises(OSError):
        ad.apply(GamepadFrame(lx=1.0))
    assert runtime.bus.events("adapter.error")[0].data == {"adapter": "broken", "error": "OSError('device unplugged')"}
