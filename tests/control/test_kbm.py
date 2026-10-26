"""Keyboard/mouse output adapter: mapping validation, press/release, mouse motion, focus gate, and Governor integration."""

import pytest
from conftest import FakeClock

from aether.control.adapters import make_adapter
from aether.control.governor import Governor
from aether.control.intent import Delegation, GamepadFrame, IntentPacket, Source
from aether.control.intent_log import IntentLog
from aether.control.kbm import DEFAULT_KBM_MAP, KbmMapping, KbmPlanner, KeyboardMouseAdapter, RecordingBackend
from aether.control.motor import MotorModel, MotorProfile
from aether.control.player import VK_NAMES
from aether.control.policy import GovernorConfig
from aether.control.safety import KillSwitch

W, S, A, D, SPACE = (VK_NAMES[k] for k in ("W", "S", "A", "D", "SPACE"))
FAST = MotorProfile(reaction_min_ms=0, reaction_max_ms=1, tremor_amp=0, drift_sigma=0)


def adapter(clock=None, focus=None, mapping=None):
    be = RecordingBackend()
    return KeyboardMouseAdapter(
        mapping or KbmMapping.from_dict(), backend=be, focus=focus, clock=clock or FakeClock()
    ), be


# ---------------------------------------------------------------- mapping
def test_default_mapping_is_valid_and_covers_both_sticks():
    m = KbmMapping.from_dict()
    targets = {t for t, _ in m.keys} | {t for t, _ in m.buttons} | {t for t, _ in m.axes}
    assert {"LX-", "LX+", "LY-", "LY+", "RX", "RY", "LT", "RT", "SOUTH"} <= targets
    assert len(DEFAULT_KBM_MAP) == len(m.keys) + len(m.buttons) + len(m.axes)


@pytest.mark.parametrize(
    "bad",
    [{"LY+": "LWIN"}, {"FOO": "W"}, {"SOUTH": "NOPE"}, {"RX": "W"}],
)
def test_bad_mappings_are_refused(bad):
    with pytest.raises(ValueError):
        KbmMapping.from_dict(bad)


def test_threshold_and_speed_bounds():
    with pytest.raises(ValueError):
        KbmMapping.from_dict(threshold=0)
    with pytest.raises(ValueError):
        KbmMapping.from_dict(mouse_px_per_s=0)


# ---------------------------------------------------------------- planner
def test_stick_directions_map_to_keys_with_threshold():
    p = KbmPlanner(KbmMapping.from_dict())
    assert p.plan(GamepadFrame(ly=0.8), 0).keys == {W}
    assert p.plan(GamepadFrame(ly=-0.8, lx=-0.9), 0).keys == {S, A}
    assert p.plan(GamepadFrame(lx=0.3), 0).keys == frozenset()  # below threshold
    assert p.plan(GamepadFrame(buttons=frozenset({"SOUTH"})), 0).keys == {SPACE}


def test_triggers_map_to_mouse_buttons():
    p = KbmPlanner(KbmMapping.from_dict())
    assert p.plan(GamepadFrame(rt=1.0, lt=1.0), 0).buttons == {"MOUSE_LEFT", "MOUSE_RIGHT"}


def test_mouse_motion_integrates_with_subpixel_remainder():
    p = KbmPlanner(KbmMapping.from_dict(mouse_px_per_s=100))
    total_x = total_y = 0
    for _ in range(120):  # one second at full right + up
        st = p.plan(GamepadFrame(rx=1.0, ry=1.0), 1 / 120)
        total_x += st.dx
        total_y += st.dy
    assert 99 <= total_x <= 100 and -100 <= total_y <= -99  # stick up moves the cursor up (negative y)


# ---------------------------------------------------------------- adapter
def test_press_release_and_neutral_releases_everything():
    c = FakeClock()
    ad, be = adapter(c)
    ad.apply(GamepadFrame(ly=0.8, rt=1.0, buttons=frozenset({"SOUTH"})))
    assert ad.keys_down == {W, SPACE} and ad.buttons_down == {"MOUSE_LEFT"}
    c.advance(0.01)
    ad.apply(GamepadFrame(ly=-0.8))  # W up before S down
    ups = [e for e in be.events if e[0] == "key" and e[2] is False]
    downs_after = be.events[be.events.index(("key", W, False)) :]
    assert ("key", W, False) in ups and ("key", S, True) in downs_after
    assert be.events.index(("key", W, False)) < be.events.index(("key", S, True))
    ad.neutral()
    assert not ad.keys_down and not ad.buttons_down
    assert ("button", "MOUSE_LEFT", False) in be.events


def test_close_releases_held_keys():
    ad, be = adapter()
    ad.apply(GamepadFrame(lx=1.0, buttons=frozenset({"SOUTH"})))
    ad.close()
    assert ("key", D, False) in be.events and ("key", SPACE, False) in be.events
    assert not ad.keys_down


def test_no_repeat_events_while_state_is_unchanged():
    c = FakeClock()
    ad, be = adapter(c)
    for _ in range(10):
        c.advance(1 / 120)
        ad.apply(GamepadFrame(ly=0.8))
    assert be.events.count(("key", W, True)) == 1


def test_focus_loss_releases_and_blocks_output():
    c = FakeClock()
    focused = {"v": True}
    ad, be = adapter(c, focus=lambda: focused["v"])
    ad.apply(GamepadFrame(ly=0.8, rx=1.0))
    focused["v"] = False
    n = len(be.events)
    for _ in range(5):
        c.advance(1 / 120)
        ad.apply(GamepadFrame(ly=0.8, rx=1.0))
    new = be.events[n:]
    assert ("key", W, False) in new
    assert not any(e[0] == "move" or (e[0] == "key" and e[2]) for e in new), "output while unfocused"
    assert ad.stats["focus_releases"] == 1


def test_make_adapter_builds_kbm_from_settings_section():
    with pytest.raises(ValueError):
        make_adapter("kbm", kbm={"map": {"SOUTH": "LWIN"}})


# ---------------------------------------------------------------- through the Governor
def _gov(tmp_path, clock, ad):
    kill = KillSwitch(tmp_path / "STOP")
    gov = Governor(GovernorConfig(), MotorModel(FAST, seed=1), ad, IntentLog(tmp_path / "kbm.jsonl"), kill,
                   lambda: True, clock=clock, seal_key=b"k" * 32)  # fmt: skip
    return gov, kill


def _ticks(gov, c, n=30):
    for _ in range(n):
        c.advance(1 / 120)
        gov.tick()


def test_undelegated_companion_output_never_presses_keys(tmp_path):
    c = FakeClock()
    ad, be = adapter(c)
    gov, _ = _gov(tmp_path, c, ad)
    pkt = IntentPacket(
        seq=1, source=Source.REFLEX, created_at=c(), ttl_ms=250, frames=(GamepadFrame(ly=1.0),), delegation_id="d1"
    )
    gov.handle("intent", pkt.to_dict())
    _ticks(gov, c)
    assert not any(e[0] == "key" and e[2] for e in be.events)


def test_delegated_output_presses_and_kill_switch_releases(tmp_path):
    c = FakeClock()
    ad, be = adapter(c)
    gov, kill = _gov(tmp_path, c, ad)
    gov.handle("grant", Delegation(id="d1", scope="full_autopilot", granted_at=c()).to_dict())
    frames = tuple(GamepadFrame(ly=1.0, buttons=frozenset({"SOUTH"})) for _ in range(16))
    pkt = IntentPacket(seq=1, source=Source.REFLEX, created_at=c(), ttl_ms=250, frames=frames, delegation_id="d1")
    gov.handle("intent", pkt.to_dict())
    _ticks(gov, c, 40)  # the motor model moves the stick at human speed
    assert W in ad.keys_down and SPACE in ad.keys_down
    kill.trip("test")
    _ticks(gov, c, 3)
    assert not ad.keys_down and not ad.buttons_down
    assert ("key", W, False) in be.events and ("key", SPACE, False) in be.events


def test_kbmtest_steps_cover_every_mapped_output():
    from aether.kbmtest import build_steps

    m = KbmMapping.from_dict()
    steps = build_steps(m)
    keys = set().union(*(s["keys"] for s in steps))
    buttons = set().union(*(s["buttons"] for s in steps))
    moves = [s["move"] for s in steps if s["move"]]
    assert keys == {vk for _, vk in m.keys} and buttons == {b for _, b in m.buttons}
    assert len(moves) == 2 * len(m.axes)  # both directions of every mouse axis
    assert steps[-1]["label"] == "Neutral"


def test_typing_mapping_gives_each_character_its_own_button():
    from aether.kbmtest import typing_mapping

    kmap, by_char = typing_mapping("hello world")
    assert set(by_char) == set("helo wrd")
    assert len(set(by_char.values())) == len(by_char)  # one button per character
    m = KbmMapping.from_dict(kmap)
    assert {VK_NAMES[k] for k in ("H", "E", "L", "O", "W", "R", "D", "SPACE")} == {vk for _, vk in m.keys}
    with pytest.raises(ValueError):
        typing_mapping("hi!")
