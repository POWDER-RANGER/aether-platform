# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Engineering scorecard E-01..E-10 (M1). Definitions here are PROPOSED; thresholds are NOT FROZEN and require owner approval (§2, §10).

Statuses follow §10 exactly. Results are appended to a JSONL ledger with run_id + evidence path; nothing is
derived from mock data.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "UNVERIFIED", "FAILED", "BLOCKED", "NOT IMPLEMENTED")


@dataclass(frozen=True)
class Criterion:
    id: str
    title: str
    measure: str
    proposed_threshold: str  # NOT FROZEN
    min_runs: int = 10


SCORECARD = (
    Criterion(
        "E-01", "Emergency stop to neutral", "STOP file / hotkey -> neutral output latency", "<= 50 ms, 10/10 runs"
    ),
    Criterion(
        "E-02",
        "Player override precedence",
        "physical input during companion output -> player wins",
        "next tick (<= 8.3 ms), 10/10",
    ),
    Criterion("E-03", "Watchdog neutralisation", "no valid intent + empty queue -> neutral", "<= 500 ms, 10/10"),
    Criterion(
        "E-04", "Intent rejection", "stale (>400 ms), replayed, forged, tampered packets rejected", "100% rejected"
    ),
    Criterion("E-05", "Intent log integrity", "hash chain + seal verify on every run", "10/10 runs verify"),
    Criterion("E-06", "Output tick stability", "Governor tick jitter at 120 Hz", "p99 interval <= 12 ms over 10 min"),
    Criterion("E-07", "Capture latency", "dxcam grab -> FrameBuffer", "median <= 10 ms, p99 <= 25 ms"),
    Criterion(
        "E-08", "Reflex non-blocking", "reflex chunk cadence unaffected while supervisor runs", "cadence change <= 10%"
    ),
    Criterion(
        "E-09", "Session reliability", "ENV-01 session without crash/unexpected exit/stall", "30 min, 10/10 sessions"
    ),
    Criterion(
        "E-10", "Recording completeness", "streams + frames present, monotonic, replayable", "10/10 runs, 0 gaps > 1 s"
    ),
)


@dataclass
class Result:
    criterion: str
    status: str
    run_ids: list[str]
    value: str
    evidence: str
    note: str = ""
    recorded: float = 0.0

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        if self.criterion not in {c.id for c in SCORECARD}:
            raise ValueError(f"unknown criterion {self.criterion}")
        self.recorded = self.recorded or time.time()


class Ledger:
    def __init__(self, path: str | Path = "evidence/scorecard.jsonl"):
        self.path = Path(path)

    def add(self, r: Result) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(r)) + "\n")

    def latest(self) -> dict[str, dict]:
        out = {c.id: {"criterion": c.id, "status": "UNVERIFIED", "title": c.title} for c in SCORECARD}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    d = json.loads(line)
                    out[d["criterion"]] = {**d, "title": out[d["criterion"]]["title"]}
        return out
