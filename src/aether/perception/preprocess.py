# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Global 256x256 reflex view and high-resolution ROI crops."""

from __future__ import annotations

import numpy as np
from PIL import Image


def reflex_view(img: np.ndarray, size: int = 256) -> np.ndarray:
    return np.asarray(Image.fromarray(img).resize((size, size), Image.BILINEAR))


def roi_crop(img: np.ndarray, box: tuple[float, float, float, float]) -> np.ndarray:
    """box normalised (x0, y0, x1, y1) in 0..1 of the full frame; returns full-res crop."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    xa, xb = sorted((int(x0 * w), int(x1 * w)))
    ya, yb = sorted((int(y0 * h), int(y1 * h)))
    if xb <= xa or yb <= ya:
        raise ValueError(f"empty ROI {box}")
    return img[ya:yb, xa:xb]


def frame_change(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute difference 0..1 on a downsampled grey view. Used by stall detection."""
    ga = np.asarray(Image.fromarray(a).convert("L").resize((64, 64)), dtype=np.float32)
    gb = np.asarray(Image.fromarray(b).convert("L").resize((64, 64)), dtype=np.float32)
    return float(np.abs(ga - gb).mean() / 255.0)
