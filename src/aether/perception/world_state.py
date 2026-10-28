# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Structured world state. Every field carries value, confidence, observed time and provenance (§6, §11).

Observed facts (reader output) and model interpretations (VLM / supervisor) stay distinguishable via
`kind`: "observed" | "interpreted".
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Fact:
    value: Any
    confidence: float
    t_mono: float
    source: str  # reader / backend name + version
    kind: str = "observed"  # observed | interpreted
    frame_seq: int | None = None


@dataclass
class WorldState:
    facts: dict[str, Fact] = field(default_factory=dict)
    phase: Fact | None = None  # e.g. menu | gameplay | loading | cutscene | paused
    objective: Fact | None = None
    threats: list[Fact] = field(default_factory=list)
    updated: float = field(default_factory=time.monotonic)

    def set(self, key: str, fact: Fact) -> None:
        self.facts[key] = fact
        self.updated = max(self.updated, fact.t_mono)

    def get(self, key: str, max_age_s: float | None = None, now: float | None = None) -> Fact | None:
        f = self.facts.get(key)
        if f is None or max_age_s is None:
            return f
        now = time.monotonic() if now is None else now
        return f if now - f.t_mono <= max_age_s else None

    def snapshot(self) -> dict:
        return asdict(self)

    def summary_text(self, now: float | None = None) -> str:
        """Compact text for a supervisor prompt; includes age and confidence so the model sees staleness."""
        now = time.monotonic() if now is None else now
        lines = []
        for k, f in sorted(self.facts.items()):
            lines.append(f"{k}={f.value!r} conf={f.confidence:.2f} age={now - f.t_mono:.1f}s src={f.source} ({f.kind})")
        if self.phase:
            lines.append(f"phase={self.phase.value} conf={self.phase.confidence:.2f}")
        if self.objective:
            lines.append(f"objective={self.objective.value!r}")
        return "\n".join(lines)
