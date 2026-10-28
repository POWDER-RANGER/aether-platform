# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Replaceable backend interfaces (§4 PR-REX, §6). Reflex = fast action chunks; Supervisor = slow goals/plans.

Registry maps a settings name to a factory. NullReflex/NullSupervisor output neutral / no plan and report
themselves as such; they exist so the loop runs end-to-end without a model and are never evidence of capability.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from aether.control.intent import GamepadFrame


@dataclass
class ReflexOutput:
    frames: list[GamepadFrame]
    confidence: float
    latency_ms: float
    backend: str
    meta: dict = field(default_factory=dict)


@dataclass
class Subgoal:
    text: str
    success_check: str | None = None  # fact key/expression, e.g. "objective_marker_visible == True"
    timeout_s: float = 30.0


@dataclass
class SupervisorOutput:
    phase: str | None
    objective: str | None
    subgoals: list[Subgoal]
    explanation: str
    confidence: float
    latency_ms: float
    backend: str
    raw: str = ""


class ReflexBackend(Protocol):
    name: str

    def act(self, view256: np.ndarray, goal: str | None, chunk_len: int) -> ReflexOutput: ...


class SupervisorBackend(Protocol):
    name: str

    def assess(self, rois: dict[str, np.ndarray], world_text: str, player_goal: str | None, history: list[str]) -> SupervisorOutput: ...


class NullReflex:
    name = "null"

    def act(self, view256, goal, chunk_len):
        return ReflexOutput([GamepadFrame.neutral() for _ in range(chunk_len)], 0.0, 0.0, self.name, {"null": True})


class NullSupervisor:
    name = "null"

    def assess(self, rois, world_text, player_goal, history):
        return SupervisorOutput(None, player_goal, [], "null supervisor: no reasoning performed", 0.0, 0.0, self.name)


REFLEX: dict[str, Callable[..., ReflexBackend]] = {"null": lambda **_: NullReflex()}
SUPERVISOR: dict[str, Callable[..., SupervisorBackend]] = {"null": lambda **_: NullSupervisor()}


def register_reflex(name: str, factory: Callable[..., ReflexBackend]) -> None:
    REFLEX[name] = factory


def register_supervisor(name: str, factory: Callable[..., SupervisorBackend]) -> None:
    SUPERVISOR[name] = factory


def make_reflex(name: str, **opts) -> ReflexBackend:
    _autoload()
    return REFLEX[name](**opts)


def make_supervisor(name: str, **opts) -> SupervisorBackend:
    _autoload()
    return SUPERVISOR[name](**opts)


def _autoload() -> None:
    # Lazy imports so optional deps don't break the registry.
    try:
        from . import ollama_vlm  # noqa: F401
    except Exception:
        pass
    try:
        from . import nitrogen_reflex  # noqa: F401
    except Exception:
        pass
