from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from aether.sim.scene import SyntheticScene


def generate() -> dict:
    scene = SyntheticScene(seed=17)
    rows = []
    for seq in (1, 30, 60, 90):
        frame = scene.frame(seq, seq / 30)
        rows.append(
            {
                "seq": seq,
                "elapsed_s": seq / 30,
                "shape": list(frame.shape),
                "health_ratio": round(scene.health_ratio(seq / 30), 6),
                "pixel_sum": int(np.asarray(frame, dtype=np.uint64).sum()),
            }
        )
    return {"kind": "SYNTHETIC", "seed": 17, "samples": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--i-reviewed-the-diff", action="store_true")
    parser.add_argument("--output", default="tests/regression/golden/scene.json")
    args = parser.parse_args()
    if not args.i_reviewed_the_diff:
        parser.error("explicit --i-reviewed-the-diff required")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(generate(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
