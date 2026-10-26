"""CLI: padtest read-back comparison logic, and a dry-run padtest that writes a verifiable log."""

from aether.cli import XINPUT_BITS, check_readback, main, padtest_steps
from aether.control.intent import GamepadFrame
from aether.control.intent_log import verify_log


def _state(**kw):
    s = {"buttons": 0, "lt": 0, "rt": 0, "lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0}
    s.update(kw)
    return s


def test_readback_accepts_matching_state():
    assert check_readback(GamepadFrame(ly=0.8), _state(ly=0.79)) is None
    assert check_readback(GamepadFrame(lt=1.0), _state(lt=255)) is None
    assert check_readback(GamepadFrame(buttons=frozenset({"SOUTH"})), _state(buttons=XINPUT_BITS["SOUTH"])) is None
    assert check_readback(GamepadFrame(), _state()) is None


def test_readback_rejects_inverted_axis_and_wrong_button():
    assert "ly" in check_readback(GamepadFrame(ly=0.8), _state(ly=-0.8))
    assert "lx" in check_readback(GamepadFrame(), _state(lx=0.5))
    assert "buttons" in check_readback(GamepadFrame(buttons=frozenset({"EAST"})), _state(buttons=XINPUT_BITS["SOUTH"]))
    assert "rt" in check_readback(GamepadFrame(rt=1.0), _state(rt=10))


def test_every_padtest_button_has_an_xinput_bit():
    for _, frame in padtest_steps():
        assert set(frame.buttons) <= set(XINPUT_BITS)


def test_dryrun_padtest_produces_valid_chained_log(tmp_path, monkeypatch):
    cfg = tmp_path / "c.yaml"
    cfg.write_text(f"log_dir: {tmp_path.as_posix()}\nstop_file: {(tmp_path / 'STOP').as_posix()}\n", encoding="utf-8")
    monkeypatch.setattr("aether.control.safety.KillSwitch.start_hotkeys", lambda self: False)
    monkeypatch.setattr("aether.control.intent_log.load_or_create_log_key", lambda *a, **k: b"k" * 32)
    assert main(["--config", str(cfg), "padtest", "--output", "dryrun", "--hold", "0.02"]) == 0
    logs = list(tmp_path.glob("padtest-*.jsonl"))
    assert len(logs) == 1
    ok, n, _, problem = verify_log(logs[0])
    assert ok and n > len(padtest_steps()), problem
