from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def append_label(path, *, run_id, frame_seq, roi, true_value, labeller, timestamp=None):
    if not run_id or frame_seq < 0 or not roi or not labeller:
        raise ValueError("required label field missing")
    row = {
        "run_id": run_id,
        "frame_seq": frame_seq,
        "roi": roi,
        "true_value": true_value,
        "labeller": labeller,
        "timestamp": timestamp or datetime.now(UTC).isoformat(),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def score_labels(labels, predictions, reader_kind):
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions length mismatch")
    if reader_kind not in {"bar", "ocr", "template"}:
        raise ValueError("unsupported reader kind")
    metric = "mae" if reader_kind == "bar" else "exact_match_rate"
    if not labels:
        return {"reader_kind": reader_kind, "count": 0, "metric": metric, "value": None}
    if reader_kind == "bar":
        value = sum(abs(float(a["true_value"]) - float(b)) for a, b in zip(labels, predictions)) / len(labels)
    else:
        value = sum(a["true_value"] == b for a, b in zip(labels, predictions)) / len(labels)
    return {"reader_kind": reader_kind, "count": len(labels), "metric": metric, "value": value}
