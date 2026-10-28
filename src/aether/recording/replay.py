# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Replay: merge a run's streams in t_mono order; list runs; summarise."""

from __future__ import annotations

import heapq
import json
from collections.abc import Iterator
from pathlib import Path


def _iter_jsonl(path: Path, tag: str) -> Iterator[tuple[float, str, dict]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                yield d.get("t_mono", 0.0), tag, d


def merged(run_dir: str | Path) -> Iterator[tuple[float, str, dict]]:
    run = Path(run_dir)
    iters = [_iter_jsonl(p, p.stem) for p in sorted((run / "streams").glob("*.jsonl"))]
    iters.append(_iter_jsonl(run / "frames.jsonl", "frame"))
    yield from heapq.merge(*iters, key=lambda x: x[0])


def list_runs(root: str | Path) -> list[dict]:
    out = []
    for m in sorted(Path(root).glob("*/manifest.json"), reverse=True):
        try:
            d = json.loads(m.read_text(encoding="utf-8"))
            d["dir"] = str(m.parent)
            out.append(d)
        except Exception as e:
            out.append({"dir": str(m.parent), "error": repr(e)})
    return out


def summarize(run_dir: str | Path) -> dict:
    counts: dict[str, int] = {}
    t0 = t1 = None
    for t, tag, _ in merged(run_dir):
        counts[tag] = counts.get(tag, 0) + 1
        t0 = t if t0 is None else t0
        t1 = t
    return {"counts": counts, "duration_s": (t1 - t0) if t0 is not None else 0.0}
