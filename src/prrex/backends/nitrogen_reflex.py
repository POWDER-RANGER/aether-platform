# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Adapter: ReflexBackend over the ported NitroGen ZMQ server client (nitrogen.py, UNVERIFIED here).

NitroGen's server speaks pickle: localhost only (see nitrogen.py docstring). Goal conditioning is ignored —
NitroGen is not goal-conditioned; that gap is a research finding to record, not hide.
"""

from __future__ import annotations

import pickle
import time

import numpy as np

from .base import ReflexOutput, register_reflex
from .nitrogen import prediction_to_frames


def build_request(image: np.ndarray) -> dict:
    """Build the documented NitroGen predict request."""
    if not isinstance(image, np.ndarray) or image.shape != (256, 256, 3) or image.dtype != np.uint8:
        raise ValueError("NitroGen image must be a 256x256 uint8 RGB numpy array")
    return {"type": "predict", "image": image}


class NitrogenReflex:
    name = "nitrogen"

    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555", timeout_ms: int = 2000):
        import zmq

        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.connect(endpoint)

    def act(self, view256: np.ndarray, goal, chunk_len):
        t0 = time.monotonic()
        # REFINE: confirm request schema against nitrogen.py's runner (it sends {"type": "predict", "image": ...}).
        self.sock.send(pickle.dumps(build_request(view256)))
        pred = pickle.loads(self.sock.recv())  # noqa: S301 — localhost-only trusted server
        frames = prediction_to_frames(pred.get("pred", pred))[:chunk_len]
        return ReflexOutput(frames, 0.5, (time.monotonic() - t0) * 1000, self.name, {"goal_conditioned": False})


register_reflex("nitrogen", lambda **o: NitrogenReflex(**o))
