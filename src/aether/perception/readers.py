# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""ROI readers. Prefer classical vision / OCR for known UI; VLM only as a fallback (§6).

Reader contract: read(crop, t_mono, frame_seq) -> Fact | None. Readers must be cheap; anything
slow belongs to the supervisor pathway, not here.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np

from .world_state import Fact


class Reader(Protocol):
    name: str

    def read(self, crop: np.ndarray, t_mono: float, frame_seq: int | None = None) -> Fact | None: ...


class BarReader:
    """Fill ratio of a horizontal bar (health/stamina style) by colour match along the middle row band."""

    def __init__(self, name: str, rgb: tuple[int, int, int], tol: int = 40, min_conf_pixels: int = 8):
        self.name, self.rgb, self.tol, self.min_px = name, np.array(rgb, dtype=np.int16), tol, min_conf_pixels

    def read(self, crop, t_mono, frame_seq=None):
        h = crop.shape[0]
        band = crop[max(0, h // 2 - 1): h // 2 + 2].astype(np.int16)
        match = (np.abs(band - self.rgb).max(axis=2) <= self.tol).any(axis=0)
        if match.sum() < self.min_px:
            return Fact(0.0, 0.3, t_mono, f"bar:{self.name}", frame_seq=frame_seq)
        cols = np.nonzero(match)[0]
        ratio = (cols.max() + 1) / match.size
        conf = float(min(1.0, match[: cols.max() + 1].mean()))  # contiguous fill -> high confidence
        return Fact(round(float(ratio), 3), conf, t_mono, f"bar:{self.name}", frame_seq=frame_seq)


class OcrReader:
    """Text via Tesseract if installed (pytesseract optional dependency). Returns None if unavailable."""

    def __init__(self, name: str, psm: int = 7, whitelist: str | None = None):
        self.name, self.psm, self.whitelist = name, psm, whitelist
        try:
            import pytesseract  # noqa: F401

            self.ok = True
        except Exception:
            self.ok = False

    def read(self, crop, t_mono, frame_seq=None):
        if not self.ok:
            return None
        import pytesseract

        cfg = f"--psm {self.psm}" + (f" -c tessedit_char_whitelist={self.whitelist}" if self.whitelist else "")
        d = pytesseract.image_to_data(crop, config=cfg, output_type=pytesseract.Output.DICT)
        words = [(w, float(c)) for w, c in zip(d["text"], d["conf"]) if w.strip() and float(c) >= 0]
        if not words:
            return Fact("", 0.0, t_mono, f"ocr:{self.name}", frame_seq=frame_seq)
        text = " ".join(w for w, _ in words)
        conf = sum(c for _, c in words) / len(words) / 100.0
        return Fact(text, conf, t_mono, f"ocr:{self.name}", frame_seq=frame_seq)


class TemplateReader:
    """Presence of a known icon by normalised cross-correlation (OpenCV optional)."""

    def __init__(self, name: str, template: np.ndarray, threshold: float = 0.8):
        self.name, self.template, self.threshold = name, template, threshold

    def read(self, crop, t_mono, frame_seq=None):
        try:
            import cv2
        except Exception:
            return None
        res = cv2.matchTemplate(crop, self.template, cv2.TM_CCOEFF_NORMED)
        score = float(res.max()) if res.size else 0.0
        return Fact(score >= self.threshold, score, t_mono, f"template:{self.name}", frame_seq=frame_seq)


def build_reader(name: str, spec: dict) -> Reader:
    t = spec.get("type")
    if t == "bar":
        return BarReader(name, tuple(spec["rgb"]), spec.get("tol", 40))
    if t == "ocr":
        return OcrReader(name, spec.get("psm", 7), spec.get("whitelist"))
    if t == "template":
        from PIL import Image

        return TemplateReader(name, np.asarray(Image.open(spec["path"]).convert("RGB")), spec.get("threshold", 0.8))
    raise ValueError(f"unknown reader type {t!r} for {name}")
