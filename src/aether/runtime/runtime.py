"""The runtime session: events, agents and tasks for one run, plus Governor observation and evidence."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from aether import __version__
from aether.control.adapters import OutputAdapter
from aether.control.intent_log import IntentLog
from aether.control.settings import Settings

from .agents import AgentRegistry
from .events import EventBus
from .evidence import work_receipt
from .governor_bridge import GovernorBridge, ObservedAdapter


def config_hash(settings: Settings) -> str:
    body = json.dumps(asdict(settings), sort_keys=True, default=str)
    return hashlib.sha256(body.encode()).hexdigest()


class Runtime:
    def __init__(
        self,
        settings: Settings,
        session_dir: str | Path,
        seal_key: bytes,
        clock: Callable[[], float] = time.monotonic,
        session_id: str | None = None,
    ):
        from .tasks import TaskBoard

        if not seal_key:
            raise ValueError("a seal key is required: every runtime session is sealed")
        self.settings = settings
        self.session_id = session_id or f"s-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.events_path = Path(session_dir) / f"events-{self.session_id}.jsonl"
        self._seal_key = seal_key
        self.store = IntentLog(self.events_path)
        self.bus = EventBus(self.session_id, self.store)
        self.agents = AgentRegistry(self.bus)
        self.tasks = TaskBoard(self.bus, self.agents, clock)
        self._producers: dict[str, str] = {}
        self._intent_logs: list[Path] = []
        self.closed = False
        self.bus.publish("session.started", "runtime", {"runtime_version": __version__,
                                                        "config_hash": config_hash(settings), "mode": settings.mode})  # fmt: skip

    def correlate(self, producer: str, task_id: str) -> None:
        """Link a Governor client's producer id to a task, so its decisions carry the task's correlation id."""
        self.tasks.get(task_id)
        self._producers[producer] = task_id

    def observe_governor(self, intent_log: IntentLog) -> None:
        """Attach read-only observation to the Governor's intent log (call before building the Governor)."""
        intent_log.add_observer(GovernorBridge(self.bus, self._producers.get))
        self._intent_logs.append(intent_log.path)

    def observe_adapter(self, adapter: OutputAdapter) -> ObservedAdapter:
        return ObservedAdapter(adapter, self.bus)

    def close(self) -> None:
        if self.closed:
            return
        self.bus.publish("session.ended", "runtime", {"events": self.bus.stats["published"] + 1})
        self.store.close(seal_key=self._seal_key)
        self.closed = True

    def receipt(self) -> dict:
        """Evidence for this session. Close the runtime (and the Governor) first so both logs are sealed."""
        if not self.closed:
            raise RuntimeError("close the runtime before producing its receipt")
        return work_receipt(self.events_path, self._intent_logs, self._seal_key)
