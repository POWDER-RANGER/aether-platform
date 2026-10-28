from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from aether.perception.preprocess import roi_crop
from aether.perception.readers import BarReader
from aether.perception.world_state import WorldState
from aether.sim.scene import SyntheticScene
from prrex.backends.base import Subgoal, SupervisorOutput
from prrex.supervisor.planner import Planner


def generate() -> dict:
    scene = SyntheticScene(seed=17)
    reader = BarReader("health", (40, 220, 80), tol=8, min_conf_pixels=1)
    samples = []
    for seq in (1, 30, 60, 90):
        elapsed = seq / 30
        frame = scene.frame(seq, elapsed)
        crop = roi_crop(frame, (12 / 320, 12 / 180, 112 / 320, 22 / 180))
        fact = reader.read(crop, elapsed, seq)
        planner = Planner(clock=lambda: 0.0)
        accepted = planner.apply(
            SupervisorOutput(
                "synthetic-phase",
                "synthetic-objective",
                [Subgoal("hold synthetic objective")],
                "synthetic golden plan",
                1.0,
                0.0,
                "synthetic-golden",
            )
        )
        goal = planner.step(WorldState())
        samples.append(
            {
                "seq": seq,
                "elapsed_s": elapsed,
                "shape": list(frame.shape),
                "health_ratio": round(scene.health_ratio(elapsed), 6),
                "pixel_sum": int(np.asarray(frame, dtype=np.uint64).sum()),
                "reader_health": fact.value if fact is not None else None,
                "reader_confidence": round(fact.confidence, 6) if fact is not None else None,
                "planner_accepted": accepted,
                "planner_goal": goal,
            }
        )
    return {"kind": "SYNTHETIC", "seed": 17, "samples": samples}


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
