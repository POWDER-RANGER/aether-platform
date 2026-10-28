# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Run identity and provenance: who/what/which versions produced a record (instructions §11)."""
from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


def _git_rev(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    except Exception:
        return "unknown"


def _git_dirty(root: Path) -> bool:
    try:
        return bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True, timeout=5).strip())
    except Exception:
        return True


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class RunIdentity:
    run_id: str = field(default_factory=lambda: time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    mode: str = "research"  # research | companion
    environment: str = "ENV-01"
    scenario: str | None = None
    git_rev: str = ""
    git_dirty: bool = True
    python: str = sys.version.split()[0]
    os: str = platform.platform()
    machine: str = platform.node()
    backends: dict = field(default_factory=dict)  # name -> {version, weights_sha256}
    settings_sha256: str = ""

    @classmethod
    def create(cls, repo_root: Path, **kw) -> RunIdentity:
        return cls(git_rev=_git_rev(repo_root), git_dirty=_git_dirty(repo_root), **kw)

    def to_dict(self) -> dict:
        return asdict(self)
