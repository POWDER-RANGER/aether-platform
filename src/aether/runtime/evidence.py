"""Work receipts: verifiable evidence for a runtime session (first runtime piece of AACP).

A receipt names each log, its SHA-256, record count, chain and seal results, and summarizes the events. It is
`ok` only if every log verifies. It contains no secrets: the seal key is used to check seals, never recorded.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from aether.control.intent_log import verify_log, verify_seal


def _log_entry(path: Path, key: bytes) -> dict:
    ok, n, last, problem = verify_log(path)
    sok, sproblem = verify_seal(path, key) if ok else (False, "chain invalid")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "records": n,
        "last_hash": last,
        "chain_ok": ok,
        "seal_ok": sok,
        "problem": problem or sproblem or None,
    }


def read_events(events_path: str | Path) -> list[dict]:
    out = []
    with Path(events_path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line)["record"]["event"])
    return out


def work_receipt(events_path: str | Path, intent_logs: list[Path], key: bytes) -> dict:
    events_path = Path(events_path)
    logs = [_log_entry(events_path, key)] + [_log_entry(Path(p), key) for p in intent_logs]
    events = read_events(events_path) if logs[0]["chain_ok"] else []
    return {
        "schema": "aether.receipt/1",
        "session_id": events[0]["session_id"] if events else None,
        "ok": all(entry["chain_ok"] and entry["seal_ok"] for entry in logs),
        "logs": logs,
        "event_counts": dict(Counter(e["type"] for e in events)),
        "first_event": events[0]["id"] if events else None,
        "last_event": events[-1]["id"] if events else None,
    }
