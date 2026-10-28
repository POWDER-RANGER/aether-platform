"""Agent identity, lifecycle and resource ownership.

An agent is a registered component with a unique id, a declared role, a set of capabilities and a version.
Its lifecycle is an explicit state machine; every accepted transition is an event, and an illegal transition
is refused without changing anything. Resources (e.g. "controller.output") are claimed exclusively; an agent
that stops or fails releases everything it held.
"""

from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum

from .events import EventBus

NAME = re.compile(r"^[a-z][a-z0-9_.-]{1,63}$")


class AgentState(str, Enum):
    REGISTERED = "registered"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


TRANSITIONS: dict[AgentState, frozenset[AgentState]] = {
    AgentState.REGISTERED: frozenset({AgentState.READY, AgentState.STOPPED, AgentState.FAILED}),
    AgentState.READY: frozenset({AgentState.RUNNING, AgentState.STOPPED, AgentState.FAILED}),
    AgentState.RUNNING: frozenset({AgentState.PAUSED, AgentState.READY, AgentState.STOPPED, AgentState.FAILED}),
    AgentState.PAUSED: frozenset({AgentState.RUNNING, AgentState.STOPPED, AgentState.FAILED}),
    AgentState.FAILED: frozenset({AgentState.READY, AgentState.STOPPED}),  # recovery is an explicit step
    AgentState.STOPPED: frozenset(),
}
AVAILABLE = (AgentState.READY, AgentState.RUNNING)


class LifecycleError(ValueError):
    pass


@dataclass
class Agent:
    name: str
    role: str
    capabilities: frozenset[str]
    version: str
    agent_id: str = field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:12]}")
    state: AgentState = AgentState.REGISTERED


class AgentRegistry:
    SOURCE = "runtime.agents"

    def __init__(self, bus: EventBus):
        self.bus = bus
        self._agents: dict[str, Agent] = {}
        self._owners: dict[str, str] = {}  # resource -> agent_id
        self._lock = threading.RLock()

    def register(self, name: str, role: str, capabilities: set[str] | frozenset[str], version: str) -> Agent:
        if not NAME.match(name):
            raise LifecycleError(f"invalid agent name: {name!r}")
        caps = frozenset(capabilities)
        if not caps or not all(NAME.match(c) for c in caps):
            raise LifecycleError(f"capabilities must be non-empty lowercase names, got {sorted(caps)}")
        if not role or not version:
            raise LifecycleError("role and version are required")
        with self._lock:
            if any(a.name == name and a.state != AgentState.STOPPED for a in self._agents.values()):
                raise LifecycleError(f"an active agent named {name!r} is already registered")
            agent = Agent(name, role, caps, version)
            self._agents[agent.agent_id] = agent
        self.bus.publish("agent.registered", self.SOURCE, {"agent_id": agent.agent_id, "name": name, "role": role,
                                                           "capabilities": sorted(caps), "version": version})  # fmt: skip
        return agent

    def get(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise LifecycleError(f"unknown agent: {agent_id}") from None

    def transition(self, agent_id: str, to: AgentState, reason: str) -> Agent:
        with self._lock:
            agent = self.get(agent_id)
            frm = agent.state
            if to not in TRANSITIONS[frm]:
                raise LifecycleError(f"{agent.name}: {frm.value} -> {to.value} is not allowed")
            agent.state = to
            ending = to in (AgentState.STOPPED, AgentState.FAILED)
            released = [r for r, owner in self._owners.items() if owner == agent_id] if ending else []
            for r in released:
                del self._owners[r]
        self.bus.publish(
            "agent.state", self.SOURCE, {"agent_id": agent_id, "from": frm.value, "to": to.value, "reason": reason}
        )
        for r in released:
            self.bus.publish("resource.released", self.SOURCE, {"resource": r, "agent_id": agent_id})
        return agent

    def discover(self, capability: str) -> list[Agent]:
        """Agents that declare `capability` and are available (ready or running)."""
        with self._lock:
            return [a for a in self._agents.values() if capability in a.capabilities and a.state in AVAILABLE]

    def claim(self, agent_id: str, resource: str) -> None:
        with self._lock:
            agent = self.get(agent_id)
            if agent.state not in AVAILABLE:
                raise LifecycleError(
                    f"{agent.name} is {agent.state.value}; only ready or running agents claim resources"
                )
            holder = self._owners.get(resource)
            conflict = holder is not None and holder != agent_id
            if not conflict:
                self._owners[resource] = agent_id
        if conflict:
            self.bus.publish(
                "resource.conflict", self.SOURCE, {"resource": resource, "agent_id": agent_id, "held_by": holder}
            )
            raise LifecycleError(f"{resource} is held by {holder}")
        self.bus.publish("resource.claimed", self.SOURCE, {"resource": resource, "agent_id": agent_id})

    def release(self, agent_id: str, resource: str) -> None:
        with self._lock:
            if self._owners.get(resource) != agent_id:
                raise LifecycleError(f"{agent_id} does not hold {resource}")
            del self._owners[resource]
        self.bus.publish("resource.released", self.SOURCE, {"resource": resource, "agent_id": agent_id})

    def owner(self, resource: str) -> str | None:
        return self._owners.get(resource)
