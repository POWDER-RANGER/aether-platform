# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Hierarchical plan with receding horizon. The supervisor proposes subgoals; the planner tracks the active one,
evaluates success checks against WorldState, times out, and asks for a replan. Never blocks the reflex loop."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from aether.perception.world_state import WorldState
from prrex.backends.base import Subgoal, SupervisorOutput


@dataclass
class PlanState:
    objective: str | None = None
    queue: list[Subgoal] = field(default_factory=list)
    active: Subgoal | None = None
    active_since: float = 0.0
    history: list[str] = field(default_factory=list)
    replan_requested: bool = True


def eval_check(check: str | None, ws: WorldState) -> bool | None:
    """Tiny safe evaluator: '<fact> <op> <literal>' with op in == != < > <= >=. None = cannot evaluate."""
    if not check:
        return None
    for op in ("<=", ">=", "==", "!=", "<", ">"):
        if op in check:
            k, v = (s.strip() for s in check.split(op, 1))
            f = ws.get(k)
            if f is None:
                return None
            lit: object = {"True": True, "False": False}.get(v, v.strip("'\""))
            try:
                lit = float(v)
            except ValueError:
                pass
            a = f.value
            try:
                return {"==": a == lit, "!=": a != lit, "<": a < lit, ">": a > lit, "<=": a <= lit, ">=": a >= lit}[op]
            except TypeError:
                return None
    return None


class Planner:
    def __init__(self, min_confidence: float = 0.4, clock=time.monotonic):
        self.s = PlanState()
        self.min_conf = min_confidence
        self.clock = clock

    def apply(self, out: SupervisorOutput) -> bool:
        """Accept a supervisor proposal if confident enough. Returns accepted."""
        if out.confidence < self.min_conf or not out.subgoals:
            self.s.history.append(f"rejected plan conf={out.confidence:.2f}")
            return False
        self.s.objective = out.objective or self.s.objective
        self.s.queue = list(out.subgoals)
        self._advance()
        self.s.replan_requested = False
        return True

    def _advance(self) -> None:
        self.s.active = self.s.queue.pop(0) if self.s.queue else None
        self.s.active_since = self.clock()
        if self.s.active is None:
            self.s.replan_requested = True

    def step(self, ws: WorldState) -> str | None:
        """Update progress. Returns the current goal text for the reflex backend (or None)."""
        a = self.s.active
        if a is None:
            return None
        ok = eval_check(a.success_check, ws)
        if ok:
            self.s.history.append(f"done: {a.text}")
            self._advance()
        elif self.clock() - self.s.active_since > a.timeout_s:
            self.s.history.append(f"timeout: {a.text}")
            self.s.replan_requested = True
            self._advance()
        return self.s.active.text if self.s.active else None
