"""Tasks: created, assigned to an agent that declares the needed capability, run, and finished.

Each task id is the correlation id of every event about it, so its whole history can be pulled from the
event log. Illegal transitions are refused. Tasks with a timeout fail when `check_timeouts` finds them late.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from .agents import AVAILABLE, AgentRegistry, LifecycleError
from .events import EventBus


class TaskState(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


TASK_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.CREATED: frozenset({TaskState.ASSIGNED, TaskState.CANCELLED}),
    TaskState.ASSIGNED: frozenset({TaskState.RUNNING, TaskState.CANCELLED, TaskState.FAILED}),
    TaskState.RUNNING: frozenset({TaskState.DONE, TaskState.FAILED, TaskState.CANCELLED}),
    TaskState.DONE: frozenset(),
    TaskState.FAILED: frozenset(),
    TaskState.CANCELLED: frozenset(),
}


@dataclass
class Task:
    kind: str
    capability: str
    created_at: float
    timeout_s: float | None = None
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}")
    state: TaskState = TaskState.CREATED
    agent_id: str | None = None
    result: dict | None = None


class TaskBoard:
    SOURCE = "runtime.tasks"

    def __init__(self, bus: EventBus, agents: AgentRegistry, clock: Callable[[], float] = time.monotonic):
        self.bus = bus
        self.agents = agents
        self.clock = clock
        self._tasks: dict[str, Task] = {}
        self._lock = threading.RLock()

    def create(self, kind: str, capability: str, timeout_s: float | None = None) -> Task:
        if not kind or not capability:
            raise LifecycleError("kind and capability are required")
        if timeout_s is not None and timeout_s <= 0:
            raise LifecycleError("timeout_s must be positive")
        t = Task(kind, capability, self.clock(), timeout_s)
        with self._lock:
            self._tasks[t.task_id] = t
        data = {"task_id": t.task_id, "kind": kind, "capability": capability}
        self.bus.publish("task.created", self.SOURCE, data, correlation_id=t.task_id)
        return t

    def get(self, task_id: str) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise LifecycleError(f"unknown task: {task_id}") from None

    def assign(self, task_id: str, agent_id: str) -> Task:
        with self._lock:
            t = self.get(task_id)
            agent = self.agents.get(agent_id)
            if t.capability not in agent.capabilities:
                raise LifecycleError(f"{agent.name} does not declare {t.capability}")
            if agent.state not in AVAILABLE:
                raise LifecycleError(f"{agent.name} is {agent.state.value}")
            self._move(t, TaskState.ASSIGNED, f"assigned to {agent.name}", publish=False)
            t.agent_id = agent_id
        self.bus.publish(
            "task.assigned", self.SOURCE, {"task_id": task_id, "agent_id": agent_id}, correlation_id=task_id
        )
        return t

    def start(self, task_id: str) -> Task:
        return self._transition(task_id, TaskState.RUNNING, "started")

    def complete(self, task_id: str, result: dict | None = None) -> Task:
        t = self._transition(task_id, TaskState.DONE, "completed")
        t.result = result
        return t

    def fail(self, task_id: str, reason: str) -> Task:
        return self._transition(task_id, TaskState.FAILED, reason)

    def cancel(self, task_id: str, reason: str) -> Task:
        return self._transition(task_id, TaskState.CANCELLED, reason)

    def check_timeouts(self) -> list[Task]:
        now = self.clock()
        active = (TaskState.ASSIGNED, TaskState.RUNNING)
        late = [
            t
            for t in list(self._tasks.values())
            if t.timeout_s is not None and t.state in active and now - t.created_at > t.timeout_s
        ]
        for t in late:
            self._transition(t.task_id, TaskState.FAILED, f"timeout after {t.timeout_s} s")
        return late

    # ------------------------------------------------------------------
    def _transition(self, task_id: str, to: TaskState, reason: str) -> Task:
        with self._lock:
            return self._move(self.get(task_id), to, reason)

    def _move(self, t: Task, to: TaskState, reason: str, publish: bool = True) -> Task:
        frm = t.state
        if to not in TASK_TRANSITIONS[frm]:
            raise LifecycleError(f"task {t.task_id}: {frm.value} -> {to.value} is not allowed")
        t.state = to
        if publish:
            data = {"task_id": t.task_id, "from": frm.value, "to": to.value, "reason": reason}
            self.bus.publish("task.state", self.SOURCE, data, correlation_id=t.task_id)
        return t
