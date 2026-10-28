# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""In-process event bus. Every subsystem publishes; recording and the Command Center subscribe.

Events are plain dicts so they serialise to JSONL unchanged. Publishing never blocks on a slow
subscriber: each subscriber gets its own bounded queue; overflow drops the oldest and counts it.
"""

from __future__ import annotations

import itertools
import json
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

Event = dict


@dataclass
class Subscription:
    topics: tuple[str, ...]
    q: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=4096))
    dropped: int = 0

    def matches(self, topic: str) -> bool:
        return any(topic == t or (t.endswith("*") and topic.startswith(t[:-1])) for t in self.topics)


class EventBus:
    def __init__(self, clock: Callable[[], float] = time.monotonic, wall: Callable[[], float] = time.time):
        self._subs: list[Subscription] = []
        self._lock = threading.Lock()
        self._seq = itertools.count(1)
        self._clock, self._wall = clock, wall

    def subscribe(self, *topics: str) -> Subscription:
        s = Subscription(topics or ("*",))
        with self._lock:
            self._subs.append(s)
        return s

    def unsubscribe(self, s: Subscription) -> None:
        with self._lock:
            if s in self._subs:
                self._subs.remove(s)

    def publish(self, topic: str, **data) -> Event:
        ev = {"seq": next(self._seq), "topic": topic, "t_mono": self._clock(), "t_wall": self._wall(), **data}
        with self._lock:
            subs = list(self._subs)
        for s in subs:
            if not s.matches(topic):
                continue
            try:
                s.q.put_nowait(ev)
            except queue.Full:
                try:
                    s.q.get_nowait()
                except queue.Empty:
                    pass
                s.dropped += 1
                s.q.put_nowait(ev)
        return ev


class JsonlSink(threading.Thread):
    """Drains a subscription to a JSONL file. Stop with stop()."""

    def __init__(self, bus: EventBus, path: str | Path, *topics: str):
        super().__init__(daemon=True, name=f"jsonl-sink:{Path(path).name}")
        self.sub = bus.subscribe(*topics)
        self.path = Path(path)
        self._stop = threading.Event()
        self.bus = bus

    def run(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            while not self._stop.is_set() or not self.sub.q.empty():
                try:
                    ev = self.sub.q.get(timeout=0.1)
                except queue.Empty:
                    continue
                f.write(json.dumps(ev, default=str, separators=(",", ":")) + "\n")
                f.flush()

    def stop(self) -> None:
        self._stop.set()
        self.join(timeout=2)
        self.bus.unsubscribe(self.sub)
