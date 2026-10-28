from __future__ import annotations

import subprocess
from dataclasses import asdict

import pytest
import yaml

from aether.runtime.config import ConfigError, PlatformSettings, load_platform_settings
from aether.runtime.identity import RunIdentity, _git_dirty


def write_settings(tmp_path, data):
    path = tmp_path / "settings.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_defaults_and_environment_files_load() -> None:
    defaults = load_platform_settings(None)
    assert defaults.mode == "research"
    assert defaults.environment == "ENV-01"
    assert defaults.backends.execute_fraction == 0.5
    assert load_platform_settings("configuration/platform/ENV-01.yaml").environment == "ENV-01"
    assert load_platform_settings("configuration/platform/ENV-02.yaml").environment == "ENV-02"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(unexpected=True),
        lambda d: d["capture"].update(unexpected=True),
    ],
)
def test_unknown_top_level_and_nested_keys_rejected(tmp_path, mutate) -> None:
    data = asdict(PlatformSettings())
    data["capture"] = {"process_name": ""}
    mutate(data)
    with pytest.raises(ConfigError, match="unknown keys"):
        load_platform_settings(write_settings(tmp_path, data))


def test_schema_version_and_mode_rejected(tmp_path) -> None:
    data = {"schema_version": 999}
    with pytest.raises(ConfigError, match="schema_version"):
        load_platform_settings(write_settings(tmp_path, data))
    data = {"mode": "production"}
    with pytest.raises(ConfigError, match="mode"):
        load_platform_settings(write_settings(tmp_path, data))


@pytest.mark.parametrize("fraction", [0, -0.1, 1.01, 2])
def test_execute_fraction_bounds(tmp_path, fraction) -> None:
    with pytest.raises(ConfigError, match="execute_fraction"):
        load_platform_settings(write_settings(tmp_path, {"backends": {"execute_fraction": fraction}}))


def test_settings_hash_is_stable_and_changes_with_value() -> None:
    first = PlatformSettings()
    same = PlatformSettings()
    changed = PlatformSettings(mode="companion")
    assert first.sha256() == same.sha256()
    assert first.sha256() != changed.sha256()


def test_git_helpers_fail_closed_outside_repository(monkeypatch, tmp_path) -> None:
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0])

    monkeypatch.setattr(subprocess, "check_output", fail)
    assert _git_rev(tmp_path) == "unknown"
    assert _git_dirty(tmp_path) is True
    ident = RunIdentity.create(tmp_path)
    assert ident.git_rev == "unknown"
    assert ident.git_dirty is True


def test_run_identity_populates_provenance_fields(tmp_path) -> None:
    ident = RunIdentity.create(tmp_path, mode="research", environment="ENV-01")
    data = ident.to_dict()
    assert data["run_id"]
    assert data["mode"] == "research"
    assert data["environment"] == "ENV-01"
    assert data["python"]
    assert data["os"]
    assert data["machine"]
