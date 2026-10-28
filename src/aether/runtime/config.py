# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Versioned platform settings schema. Loads YAML, validates, refuses unknown keys.

Separate from aether.control.settings (Governor settings, already verified) — this file covers the
platform: capture, perception, backends, recording, server. Bump SCHEMA_VERSION on breaking change.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

import yaml

SCHEMA_VERSION = 1


class ConfigError(ValueError):
    pass


@dataclass
class CaptureCfg:
    process_name: str = ""
    target_fps: int = 60
    buffer_seconds: float = 2.0
    reflex_size: int = 256


@dataclass
class PerceptionCfg:
    rois: dict = field(default_factory=dict)  # name -> [x0,y0,x1,y1] normalised 0..1
    readers: dict = field(default_factory=dict)  # name -> {type: bar|ocr|vlm, ...}


@dataclass
class BackendCfg:
    reflex: str = "null"  # registry name
    supervisor: str = "null"
    reflex_options: dict = field(default_factory=dict)
    supervisor_options: dict = field(default_factory=dict)
    supervisor_period_s: float = 2.0
    chunk_len: int = 16
    execute_fraction: float = 0.5  # receding horizon: act on this fraction of a chunk, then replan


@dataclass
class RecordingCfg:
    root: str = "runs"
    frame_every_n: int = 6
    jpeg_quality: int = 85


@dataclass
class ServerCfg:
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class PlatformSettings:
    schema_version: int = SCHEMA_VERSION
    mode: str = "research"
    environment: str = "ENV-01"
    governor_endpoint: str = "tcp://127.0.0.1:5560"
    capture: CaptureCfg = field(default_factory=CaptureCfg)
    perception: PerceptionCfg = field(default_factory=PerceptionCfg)
    backends: BackendCfg = field(default_factory=BackendCfg)
    recording: RecordingCfg = field(default_factory=RecordingCfg)
    server: ServerCfg = field(default_factory=ServerCfg)

    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def _build(cls, data: dict, path: str):
    known = {f.name: f for f in fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ConfigError(f"{path}: unknown keys {sorted(unknown)}")
    kw = {}
    for name, val in data.items():
        default = known[name].default_factory() if callable(known[name].default_factory) else None  # type: ignore[misc]
        if default is not None and hasattr(default, "__dataclass_fields__"):
            if not isinstance(val, dict):
                raise ConfigError(f"{path}.{name}: expected mapping")
            kw[name] = _build(type(default), val, f"{path}.{name}")
        else:
            kw[name] = val
    return cls(**kw)


def load_platform_settings(path: str | Path | None) -> PlatformSettings:
    if path is None:
        return PlatformSettings()
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    s = _build(PlatformSettings, data, "settings")
    if s.schema_version != SCHEMA_VERSION:
        raise ConfigError(f"schema_version {s.schema_version} != {SCHEMA_VERSION}")
    if s.mode not in ("research", "companion"):
        raise ConfigError("mode must be research|companion")
    if not 0 < s.backends.execute_fraction <= 1:
        raise ConfigError("backends.execute_fraction must be in (0, 1]")
    return s
