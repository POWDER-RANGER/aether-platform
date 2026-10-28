"""Typed, versioned events with local, hash-chained persistence.

Every event has a schema version, a unique id, wall and monotonic timestamps, the session id, an optional
correlation id (e.g. the task it belongs to) and causation id (the event that led to it), a source component
and a data payload whose required fields depend on the event type. Events are written to an append-only,
hash-chained log (the same format and `aether verify-log` tooling as the Governor's intent log) before
subscribers see them.

The bus records and distributes; it never authorizes. Nothing that decides controller output listens to it.
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from aether.control.intent_log import IntentLog

SCHEMA = "aether.event/1"

# type -> required data fields. A type not listed here cannot be published.
EVENT_TYPES: dict[str, frozenset[str]] = {
    k: frozenset(v)
    for k, v in {
        "session.started": {"runtime_version", "config_hash", "mode"},
        "session.ended": {"events"},
        "agent.registered": {"agent_id", "name", "role", "capabilities", "version"},
        "agent.state": {"agent_id", "from", "to", "reason"},
        "resource.claimed": {"resource", "agent_id"},
        "resource.released": {"resource", "agent_id"},
        "resource.conflict": {"resource", "agent_id", "held_by"},
        "task.created": {"task_id", "kind", "capability"},
        "task.assigned": {"task_id", "agent_id"},
        "task.state": {"task_id", "from", "to", "reason"},
        "governor.session": {"phase"},
        "governor.decision": {"allow", "reasons", "source", "seq", "producer"},
        "governor.override": {"seq", "producer"},
        "governor.focus_block": {"seq", "producer"},
        "governor.rejected": {"reason"},
        "governor.grant": {"delegation", "refused"},
        "governor.revoke": {"id"},
        "governor.halt": {"reason"},
        "governor.resume": {"how"},
        "governor.watchdog": {"note"},
        "governor.player_command": set(),
        "governor.record": {"kind"},
        "adapter.active": {"adapter"},
        "adapter.neutral": {"adapter"},
        "adapter.error": {"adapter", "error"},
        "bus.subscriber_error": {"subscriber", "event_type", "error"},
    }.items()
}

_SECRET_NAME = re.compile(r"(^|_)(key|token|secret|password|passwd|credential)s?$", re.IGNORECASE)
REDACTED = "[redacted]"


def redact(value: Any) -> Any:
    """Replace values stored under secret-looking names, at any depth."""
    if isinstance(value, dict):
        return {k: (REDACTED if _SECRET_NAME.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


@dataclass(frozen=True)
class Event:
    type: str
    source: str
    data: dict
    session_id: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts_wall: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="microseconds"))
    ts_mono: float = field(default_factory=time.monotonic)
    correlation_id: str | None = None
    causation_id: str | None = None
    schema: str = SCHEMA

    def to_dict(self) -> dict:
        return asdict(self)


class EventBus:
    def __init__(self, session_id: str, store: IntentLog | None, keep: int = 50_000):
        if not session_id:
            raise ValueError("session_id is required")
        self.session_id = session_id
        self.store = store
        self.keep = keep
        self._lock = threading.RLock()
        self._subs: list[tuple[Callable[[Event], None], frozenset[str] | None]] = []
        self._history: list[Event] = []
        self.stats = {"published": 0, "subscriber_errors": 0}

    def subscribe(self, fn: Callable[[Event], None], types: set[str] | None = None) -> None:
        if types is not None:
            unknown = set(types) - set(EVENT_TYPES)
            if unknown:
                raise ValueError(f"unknown event types: {sorted(unknown)}")
        self._subs.append((fn, frozenset(types) if types else None))

    def publish(
        self,
        type: str,
        source: str,
        data: dict,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> Event:
        if type not in EVENT_TYPES:
            raise ValueError(f"unknown event type: {type}")
        missing = EVENT_TYPES[type] - set(data)
        if missing:
            raise ValueError(f"{type}: missing fields {sorted(missing)}")
        if not source:
            raise ValueError("source is required")
        clean = redact(data)
        try:
            clean = json.loads(json.dumps(clean, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{type}: data is not plain JSON: {exc}") from exc
        ev = Event(type, source, clean, self.session_id, correlation_id=correlation_id, causation_id=causation_id)
        with self._lock:
            if self.store is not None:
                self.store.append(type, event=ev.to_dict())  # persisted before anyone sees it
            self._history.append(ev)
            if len(self._history) > self.keep:
                del self._history[: len(self._history) - self.keep]
            self.stats["published"] += 1
            subs = list(self._subs)
        for fn, types in subs:
            if types is not None and type not in types:
                continue
            try:
                fn(ev)
            except Exception as exc:  # a subscriber cannot break publishing or other subscribers
                self.stats["subscriber_errors"] += 1
                if type != "bus.subscriber_error":
                    self.publish("bus.subscriber_error", "bus", {"subscriber": getattr(fn, "__name__", repr(fn)),
                                                                  "event_type": type, "error": repr(exc)})  # fmt: skip
        return ev

    def events(self, type: str | None = None, correlation_id: str | None = None) -> list[Event]:
        with self._lock:
            return [
                e
                for e in self._history
                if (type is None or e.type == type) and (correlation_id is None or e.correlation_id == correlation_id)
            ]
