# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Component lifecycle: ordered start, reverse stop, health, and lifecycle events on the bus."""

from __future__ import annotations

import threading
import time
from enum import Enum

from .events import EventBus


class State(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class Component:
    name = "component"

    def __init__(self, bus: EventBus):
        self.bus = bus
        self.state = State.CREATED
        self.error: str | None = None

    def _set(self, st: State, **extra) -> None:
        self.state = st
        self.bus.publish("lifecycle", component=self.name, state=st.value, **extra)

    def start(self) -> None: ...
    def stop(self) -> None: ...

    def health(self) -> dict:
        return {"state": self.state.value, "error": self.error}


class ThreadedComponent(Component):
    """Component that runs loop_once() repeatedly on its own thread until stopped."""

    period_s = 0.0

    def __init__(self, bus: EventBus):
        super().__init__(bus)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.iterations = 0

    def loop_once(self) -> None:
        raise NotImplementedError

    def _run(self) -> None:
        try:
            while not self._stop.is_set():
                t0 = time.monotonic()
                self.loop_once()
                self.iterations += 1
                dt = self.period_s - (time.monotonic() - t0)
                if dt > 0:
                    self._stop.wait(dt)
        except Exception as e:  # surface, never swallow
            self.error = repr(e)
            self._set(State.FAILED, error=self.error)

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name=self.name)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)


class Runtime:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.components: list[Component] = []

    def add(self, c: Component) -> Component:
        self.components.append(c)
        return c

    def start(self) -> None:
        for c in self.components:
            c._set(State.STARTING)
            try:
                c.start()
                c._set(State.RUNNING)
            except Exception as e:
                c.error = repr(e)
                c._set(State.FAILED, error=c.error)
                self.stop()
                raise

    def stop(self) -> None:
        for c in reversed(self.components):
            if c.state in (State.RUNNING, State.STARTING, State.FAILED):
                c._set(State.STOPPING)
                try:
                    c.stop()
                finally:
                    c._set(State.STOPPED)

    def health(self) -> dict:
        return {c.name: c.health() for c in self.components}
