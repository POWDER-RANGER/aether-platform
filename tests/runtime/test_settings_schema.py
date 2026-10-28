"""Versioned settings: unknown keys, wrong versions and invalid values are refused (fail closed)."""

from pathlib import Path

import pytest

from aether.control.settings import SCHEMA_VERSION, ConfigError, load_settings

REPO = Path(__file__).resolve().parents[2]


def write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_shipped_default_and_profiles_are_valid():
    assert SCHEMA_VERSION == 1
    load_settings()
    for prof in (REPO / "configuration" / "profiles").glob("*.yaml"):
        load_settings(profile_path=prof)


@pytest.mark.parametrize(
    "text,match",
    [
        ("schema_version: 2\n", "schema_version"),
        ("tick_rate: 120\n", "unknown settings"),
        ("tick_hz: 0\n", "tick_hz"),
        ("tick_hz: fast\n", "tick_hz"),
        ("output: joystick\n", "output"),
        ("mode: autopilot\n", "mode"),
        ("endpoint: tcp://0.0.0.0:5577\n", "localhost"),
        ("governor: 5\n", "governor must be a mapping"),
        ("- just\n- a list\n", "mapping"),
    ],
)
def test_invalid_settings_are_refused(tmp_path, text, match):
    with pytest.raises(ConfigError, match=match):
        load_settings(write(tmp_path, text))


def test_unknown_key_in_a_profile_is_refused(tmp_path):
    prof = write(tmp_path, "name: p\nmotr:\n  reaction_median_ms: 200\n")
    with pytest.raises(ConfigError, match="motr"):
        load_settings(profile_path=prof)


def test_config_error_is_a_value_error():
    assert issubclass(ConfigError, ValueError)
