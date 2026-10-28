# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Scenario definitions (SCN-xx formal, DG-xx diagnostic) loaded from configuration/scenarios/*.yaml,
and threshold freezing: a frozen file's sha256 is written to a lock; later edits are detected (§10)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Scenario:
    id: str
    title: str
    kind: str  # formal | diagnostic
    environment: str
    modes: list[str]
    setup: str
    success: list[str]
    failure: list[str]
    metrics: list[str]
    thresholds: dict = field(default_factory=dict)
    runs_required: int = 10
    time_limit_s: float = 900


def load_scenarios(root: str | Path = "configuration/scenarios") -> dict[str, Scenario]:
    out = {}
    for p in sorted(Path(root).glob("*.yaml")):
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        out[d["id"]] = Scenario(**d)
    return out


def freeze(root: str | Path = "configuration/scenarios", lock: str | Path = "evidence/thresholds.lock.json") -> dict:
    digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).glob("*.yaml"))}
    Path(lock).parent.mkdir(parents=True, exist_ok=True)
    Path(lock).write_text(json.dumps(digests, indent=2), encoding="utf-8")
    return digests


def check_frozen(
    root: str | Path = "configuration/scenarios", lock: str | Path = "evidence/thresholds.lock.json"
) -> list[str]:
    """Returns names of scenario files changed since freezing. Non-empty => formal results invalid."""
    frozen = json.loads(Path(lock).read_text(encoding="utf-8"))
    changed = [
        n
        for n, h in frozen.items()
        if not (Path(root) / n).exists() or hashlib.sha256((Path(root) / n).read_bytes()).hexdigest() != h
    ]
    return changed
