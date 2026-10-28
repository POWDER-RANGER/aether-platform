"""Agent identity and lifecycle, resource ownership, and tasks."""

import pytest

from aether.runtime import AgentState, LifecycleError, TaskState


def ready_agent(rt, name="prrex.reflex", caps=("controller.propose",)):
    a = rt.agents.register(name, "reflex", set(caps), "0.1.0")
    rt.agents.transition(a.agent_id, AgentState.READY, "initialized")
    return a


def test_register_gives_unique_identity_and_emits_event(runtime):
    a = runtime.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")
    b = runtime.agents.register("prrex.supervisor", "supervisor", {"plan"}, "0.1.0")
    assert a.agent_id != b.agent_id and a.state == AgentState.REGISTERED
    ev = runtime.bus.events("agent.registered")[0]
    assert ev.data["agent_id"] == a.agent_id and ev.data["capabilities"] == ["controller.propose"]


@pytest.mark.parametrize("name,caps", [("Bad Name", {"x.y"}), ("ok.name", set()), ("ok.name", {"Upper"})])
def test_invalid_registration_is_refused(runtime, name, caps):
    with pytest.raises(LifecycleError):
        runtime.agents.register(name, "r", caps, "1")
    assert not runtime.bus.events("agent.registered")


def test_duplicate_active_name_is_refused(runtime):
    ready_agent(runtime)
    with pytest.raises(LifecycleError):
        runtime.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")


def test_lifecycle_transitions_are_enforced(runtime):
    a = ready_agent(runtime)
    for to in (
        AgentState.RUNNING,
        AgentState.PAUSED,
        AgentState.RUNNING,
        AgentState.FAILED,
        AgentState.READY,
        AgentState.STOPPED,
    ):
        runtime.agents.transition(a.agent_id, to, "test")
    with pytest.raises(LifecycleError):
        runtime.agents.transition(a.agent_id, AgentState.READY, "stopped is final")
    states = [e.data["to"] for e in runtime.bus.events("agent.state")]
    assert states == ["ready", "running", "paused", "running", "failed", "ready", "stopped"]


def test_illegal_transition_changes_nothing(runtime):
    a = runtime.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")
    with pytest.raises(LifecycleError):
        runtime.agents.transition(a.agent_id, AgentState.PAUSED, "not running")
    assert a.state == AgentState.REGISTERED and not runtime.bus.events("agent.state")


def test_discover_returns_only_available_agents_with_the_capability(runtime):
    a = ready_agent(runtime)
    runtime.agents.register("prrex.idle", "reflex", {"controller.propose"}, "0.1.0")  # registered, not ready
    ready_agent(runtime, "prrex.planner", ("plan",))
    assert [x.agent_id for x in runtime.agents.discover("controller.propose")] == [a.agent_id]
    runtime.agents.transition(a.agent_id, AgentState.FAILED, "crash")
    assert runtime.agents.discover("controller.propose") == []


def test_resources_are_exclusive_and_released_on_stop_or_failure(runtime):
    a = ready_agent(runtime)
    b = ready_agent(runtime, "prrex.other")
    runtime.agents.claim(a.agent_id, "controller.output")
    with pytest.raises(LifecycleError, match="held by"):
        runtime.agents.claim(b.agent_id, "controller.output")
    assert runtime.bus.events("resource.conflict")[0].data["held_by"] == a.agent_id
    runtime.agents.transition(a.agent_id, AgentState.FAILED, "crash")
    assert runtime.agents.owner("controller.output") is None
    assert runtime.bus.events("resource.released")[0].data == {"resource": "controller.output", "agent_id": a.agent_id}
    runtime.agents.claim(b.agent_id, "controller.output")
    assert runtime.agents.owner("controller.output") == b.agent_id


def test_unavailable_agent_cannot_claim(runtime):
    a = runtime.agents.register("prrex.reflex", "reflex", {"controller.propose"}, "0.1.0")
    with pytest.raises(LifecycleError):
        runtime.agents.claim(a.agent_id, "controller.output")


def test_task_lifecycle_and_correlation(runtime):
    a = ready_agent(runtime)
    t = runtime.tasks.create("drive", "controller.propose")
    runtime.tasks.assign(t.task_id, a.agent_id)
    runtime.tasks.start(t.task_id)
    runtime.tasks.complete(t.task_id, {"frames": 3})
    assert t.state == TaskState.DONE and t.result == {"frames": 3}
    types = [e.type for e in runtime.bus.events(correlation_id=t.task_id)]
    assert types == ["task.created", "task.assigned", "task.state", "task.state"]
    with pytest.raises(LifecycleError):
        runtime.tasks.start(t.task_id)  # done is final


def test_task_needs_a_capable_available_agent(runtime):
    planner = ready_agent(runtime, "prrex.planner", ("plan",))
    idle = runtime.agents.register("prrex.idle", "reflex", {"controller.propose"}, "0.1.0")
    t = runtime.tasks.create("drive", "controller.propose")
    with pytest.raises(LifecycleError, match="does not declare"):
        runtime.tasks.assign(t.task_id, planner.agent_id)
    with pytest.raises(LifecycleError, match="registered"):
        runtime.tasks.assign(t.task_id, idle.agent_id)
    assert t.state == TaskState.CREATED


def test_task_timeout_fails_the_task(runtime, clock):
    a = ready_agent(runtime)
    t = runtime.tasks.create("drive", "controller.propose", timeout_s=5)
    runtime.tasks.assign(t.task_id, a.agent_id)
    runtime.tasks.start(t.task_id)
    clock.advance(4)
    assert runtime.tasks.check_timeouts() == []
    clock.advance(2)
    assert runtime.tasks.check_timeouts() == [t] and t.state == TaskState.FAILED
    assert "timeout" in runtime.bus.events("task.state")[-1].data["reason"]


def test_cancel(runtime):
    t = runtime.tasks.create("drive", "controller.propose")
    runtime.tasks.cancel(t.task_id, "owner cancelled")
    assert t.state == TaskState.CANCELLED
