"""Repository boundaries from docs/security/SECRETS-POLICY.md: forbidden files are ignored and none are tracked."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = [
    "weights/ng.pt",
    "model.safetensors",
    "checkpoints/run.ckpt",
    "model.onnx",
    "model.gguf",
    "log.key",
    "config/signing.pem",
    "STOP",
    ".env",
    ".env.local",
    "ENVIRONMENT.md",
    "logs/session.jsonl",
    "recordings/run-001.mp4",
    "debug.log",
]
FORBIDDEN_SUFFIXES = (".pt", ".pth", ".ckpt", ".safetensors", ".onnx", ".gguf", ".key", ".pem")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("path", FORBIDDEN)
def test_forbidden_path_is_ignored(path):
    assert _git("check-ignore", "--no-index", "-q", path).returncode == 0, f"{path} is not ignored"


def test_no_forbidden_file_is_tracked():
    tracked = _git("ls-files").stdout.splitlines()
    bad = [f for f in tracked if f.endswith(FORBIDDEN_SUFFIXES) or Path(f).name in {"STOP", ".env", "ENVIRONMENT.md"}]
    assert not bad, bad


def test_public_docs_have_no_personal_paths():
    hits = _git("grep", "-n", "-i", "-E", r"C:\\Users\\[a-z0-9_]+\\").stdout.strip()
    assert not hits, hits
