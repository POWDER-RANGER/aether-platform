"""Governor observation: turns the Governor's own intent-log records into typed runtime events.

This is observe-only by construction:
  - it is attached as an IntentLog observer, which receives a copy of each record after it is written,
    runs outside the log lock, and whose exceptions are swallowed by the log;
  - it never calls into the Governor, the policy or the adapter;
  - the Governor runs exactly the same code with or without it.

ObservedAdapter wraps an output adapter to report delivered output (active / neutral transitions) and
adapter failures. It forwards every call unchanged and re-raises every error.
"""

from __future__ import annotations

from collections.abc import Callable

from aether.control.adapters import OutputAdapter
from aether.control.intent import GamepadFrame

from .events import EventBus

SOURCE = "control.governor"

_SIMPLE = {
    "rejected_message": ("governor.rejected", ("reason",)),
    "grant": ("governor.grant", ("delegation", "refused")),
    "revoke": ("governor.revoke", ("id",)),
    "kill_switch": ("governor.halt", ("reason", "delegations_revoked")),
    "resume": ("governor.resume", ("how", "note")),
    "watchdog": ("governor.watchdog", ("note",)),
    "player_command": ("governor.player_command", ("id", "verb", "target", "manner", "scope", "text", "via")),
}


class GovernorBridge:
    def __init__(self, bus: EventBus, correlate: Callable[[str | None], str | None] = lambda producer: None):
        self.bus = bus
        self.correlate = correlate

    def __call__(self, record: dict) -> None:
        kind = record.get("kind")
        ref = {"intent_log_n": record.get("n")}
        if kind == "intent":
            producer = record.get("producer")
            corr = self.correlate(producer)
            data = {
                k: record.get(k)
                for k in ("allow", "reasons", "source", "seq", "producer", "delegation_id", "frames", "note")
            }
            ev = self.bus.publish("governor.decision", SOURCE, data | ref, correlation_id=corr)
            reasons = " ".join(record.get("reasons") or [])
            if not record.get("allow") and "player override" in reasons:
                self.bus.publish("governor.override", SOURCE, {"seq": data["seq"], "producer": producer} | ref,
                                 correlation_id=corr, causation_id=ev.id)  # fmt: skip
            if not record.get("allow") and "not in front" in reasons:
                self.bus.publish("governor.focus_block", SOURCE, {"seq": data["seq"], "producer": producer} | ref,
                                 correlation_id=corr, causation_id=ev.id)  # fmt: skip
        elif kind in ("session_start", "session_end"):
            phase = "start" if kind == "session_start" else "end"
            extra = {"adapter": record.get("adapter")} if phase == "start" else {"stats": record.get("stats")}
            self.bus.publish("governor.session", SOURCE, {"phase": phase} | extra | ref)
        elif kind in _SIMPLE:
            etype, keys = _SIMPLE[kind]
            self.bus.publish(etype, SOURCE, {k: record.get(k) for k in keys} | ref)
        else:
            self.bus.publish("governor.record", SOURCE, {"kind": kind} | ref)


class ObservedAdapter(OutputAdapter):
    """Pass-through wrapper: reports what was delivered and any adapter failure; changes nothing."""

    def __init__(self, inner: OutputAdapter, bus: EventBus):
        self.inner = inner
        self.bus = bus
        self.name = inner.name
        self._active = False

    def apply(self, frame: GamepadFrame) -> None:
        try:
            self.inner.apply(frame)
        except Exception as exc:
            self.bus.publish("adapter.error", "control.adapter", {"adapter": self.name, "error": repr(exc)})
            raise
        active = frame != GamepadFrame.neutral()
        if active != self._active:
            self._active = active
            data = {"adapter": self.name} | ({"frame": frame.to_dict()} if active else {})
            self.bus.publish("adapter.active" if active else "adapter.neutral", "control.adapter", data)

    def neutral(self) -> None:
        self.apply(GamepadFrame.neutral())

    def close(self) -> None:
        try:
            self.inner.close()
        except Exception as exc:
            self.bus.publish("adapter.error", "control.adapter", {"adapter": self.name, "error": repr(exc)})
            raise
        if self._active:
            self._active = False
            self.bus.publish("adapter.neutral", "control.adapter", {"adapter": self.name})

    def __getattr__(self, item):  # e.g. DryRunAdapter.frames
        return getattr(self.inner, item)
