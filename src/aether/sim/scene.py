"""Seeded synthetic RGB scene generator. Every rendered element is SYNTHETIC."""

from __future__ import annotations

import numpy as np


class SyntheticScene:
    """Create deterministic synthetic frames; no real application is modeled."""

    SYNTHETIC = True

    def __init__(self, seed: int = 7, width: int = 320, height: int = 180, drain_per_s: float = 0.01):
        self.seed, self.width, self.height, self.drain_per_s = seed, width, height, drain_per_s
        self.rng = np.random.default_rng(seed)

    def health_ratio(self, elapsed_s: float) -> float:
        return max(0.0, 1.0 - max(0.0, elapsed_s) * self.drain_per_s)

    def frame(self, seq: int, elapsed_s: float) -> np.ndarray:
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        image[:] = (18, 24, 32)
        x = 12 + (int(elapsed_s * 30) % max(1, self.width - 40))
        image[65:85, x : x + 20] = (40, 180, 230)
        image[12:22, 12:112] = (45, 45, 45)
        fill = int(round(98 * self.health_ratio(elapsed_s)))
        image[14:20, 13 : 13 + fill] = (40, 220, 80)
        image[110:130, 14:100] = (210, 210, 210)
        image[145:155, 270:280] = (240, 180, 30)
        if seq % 7 == 0:
            image[30:32, 200:220] = (int(self.rng.integers(1, 255)), 80, 80)
        return image
