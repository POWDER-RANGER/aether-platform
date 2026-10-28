from __future__ import annotations

import builtins
import threading
import time

import numpy as np
import pytest

from aether.perception.frame_buffer import Frame, FrameBuffer
from aether.perception.pipeline import PerceptionPipeline
from aether.perception.preprocess import frame_change, reflex_view, roi_crop
from aether.perception.readers import BarReader, OcrReader, TemplateReader, build_reader
from aether.perception.world_state import Fact, WorldState
from aether.runtime.topics import TopicBus


def synthetic_frame(fill: float = 0.5) -> np.ndarray:
    """Return a synthetic RGB bar fixture; this is not a captured screen image."""
    image = np.zeros((20, 100, 3), dtype=np.uint8)
    image[:, : int(100 * fill)] = (200, 200, 200)
    return image


def test_frame_buffer_capacity_latest_and_window() -> None:
    buf = FrameBuffer(capacity=2)
    assert buf.latest() is None
    first = buf.push(1.0, synthetic_frame(), source="synthetic")
    buf.push(2.0, synthetic_frame(), source="synthetic")
    third = buf.push(3.0, synthetic_frame(), source="synthetic")
    assert buf.latest().seq == third.seq
    assert first.seq == 1
    assert [frame.seq for frame in buf.window(1.5)] == [2, 3]


def test_wait_newer_timeout_and_wakeup() -> None:
    buf = FrameBuffer()
    assert buf.wait_newer(0, timeout=0.01) is None
    result = []

    def producer():
        time.sleep(0.03)
        result.append(buf.push(1.0, synthetic_frame(), source="synthetic"))

    thread = threading.Thread(target=producer)
    thread.start()
    received = buf.wait_newer(0, timeout=1.0)
    thread.join()
    assert received is result[0]


def test_preprocess_reflex_shape_roi_bounds_and_frame_change() -> None:
    image = synthetic_frame(0.5)
    assert reflex_view(image).shape == (256, 256, 3)
    crop = roi_crop(image, (0.8, 0.8, 0.2, 0.2))
    assert crop.shape == (12, 60, 3)
    with pytest.raises(ValueError, match="empty ROI"):
        roi_crop(image, (0.2, 0.2, 0.2, 0.8))
    assert frame_change(image, image.copy()) == 0
    assert frame_change(image, synthetic_frame(1.0)) > 0


@pytest.mark.parametrize(("fill", "expected"), [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)])
def test_bar_reader_synthetic_fill_levels(fill, expected) -> None:
    fact = BarReader("synthetic-bar", (200, 200, 200)).read(synthetic_frame(fill), 1.0)
    assert fact is not None
    assert fact.value == pytest.approx(expected, abs=0.02)


def test_world_state_age_and_summary_provenance() -> None:
    state = WorldState()
    state.set("health", Fact(0.75, 0.9, 10.0, "synthetic-reader", "observed"))
    state.set("intent", Fact("advance", 0.6, 9.0, "synthetic-model", "interpreted"))
    assert state.get("health", max_age_s=2, now=11) is not None
    assert state.get("health", max_age_s=0.5, now=11) is None
    text = state.summary_text(now=12)
    assert "conf=0.90" in text
    assert "age=2.0s" in text
    assert "(observed)" in text
    assert "(interpreted)" in text


def test_optional_ocr_and_template_readers_return_none_when_missing(monkeypatch) -> None:
    original_import = builtins.__import__

    def no_optional(name, *args, **kwargs):
        if name in {"pytesseract", "cv2"}:
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_optional)
    assert OcrReader("ocr").read(synthetic_frame(), 1.0) is None
    assert TemplateReader("template", synthetic_frame()).read(synthetic_frame(), 1.0) is None


def test_build_reader_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="unknown reader type"):
        build_reader("unknown", {"type": "unknown"})


def test_pipeline_updates_world_state_and_publishes_each_fact() -> None:
    bus = TopicBus()
    events = bus.subscribe("perception.fact")
    pipeline = PerceptionPipeline(
        bus,
        {"bar": [0, 0, 1, 1], "second": [0, 0, 1, 1]},
        {"bar": {"type": "bar", "rgb": [200, 200, 200]}, "second": {"type": "bar", "rgb": [200, 200, 200]}},
    )
    frame = Frame(1, 1.0, synthetic_frame(0.5), "synthetic")
    state = pipeline.process(frame)
    assert state.get("bar") is not None
    assert state.get("second") is not None
    assert events.q.qsize() == 2
