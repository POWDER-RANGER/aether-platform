# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Perception pipeline: frame -> ROI readers -> WorldState, publishing perception events."""

from __future__ import annotations

from aether.runtime.topics import TopicBus

from .frame_buffer import Frame
from .preprocess import roi_crop
from .readers import Reader, build_reader
from .world_state import WorldState


class PerceptionPipeline:
    def __init__(self, bus: TopicBus, rois: dict, reader_specs: dict):
        self.bus = bus
        self.rois = {k: tuple(v) for k, v in rois.items()}
        self.readers: dict[str, Reader] = {name: build_reader(name, spec) for name, spec in reader_specs.items()}
        self.state = WorldState()

    def process(self, frame: Frame) -> WorldState:
        for name, reader in self.readers.items():
            roi = self.rois.get(name)
            if roi is None:
                continue
            fact = reader.read(roi_crop(frame.image, roi), frame.t_mono, frame.seq)
            if fact is not None:
                self.state.set(name, fact)
                self.bus.publish(
                    "perception.fact",
                    key=name,
                    value=fact.value,
                    confidence=fact.confidence,
                    source=fact.source,
                    frame_seq=frame.seq,
                )
        return self.state
