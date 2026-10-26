"""Æther command line: python -m aether <command>

  padtest     drive the virtual pad through a labelled test pattern through the Governor;
              with --readback, read each step back over XInput and fail on any mismatch (Windows, X360)
  verify-log  verify an intent log's hash chain and seal
  stop        trip the kill switch by creating the STOP file

Adapted from the reference repository's CLI (powder_ranger/cli.py @ ad15296); launch, governor serving,
the reflex runner and player channels arrive with the runtime work that needs them.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import sys
import time
from pathlib import Path

from .control.intent import BUTTONS, GamepadFrame, IntentPacket, Source
from .control.settings import load_settings

BUTTON_STEPS = BUTTONS  # all 15 mapped buttons, including START, BACK, GUIDE and both thumb clicks
XINPUT_BITS = {
    "DPAD_UP": 0x0001, "DPAD_DOWN": 0x0002, "DPAD_LEFT": 0x0004, "DPAD_RIGHT": 0x0008,
    "START": 0x0010, "BACK": 0x0020, "LEFT_THUMB": 0x0040, "RIGHT_THUMB": 0x0080,
    "LEFT_SHOULDER": 0x0100, "RIGHT_SHOULDER": 0x0200, "GUIDE": 0x0400,
    "SOUTH": 0x1000, "EAST": 0x2000, "WEST": 0x4000, "NORTH": 0x8000,
}  # fmt: skip


def padtest_steps() -> list[tuple[str, GamepadFrame]]:
    return [
        ("Left stick UP", GamepadFrame(ly=0.8)),
        ("Left stick DOWN", GamepadFrame(ly=-0.8)),
        ("Left stick LEFT", GamepadFrame(lx=-0.8)),
        ("Left stick RIGHT", GamepadFrame(lx=0.8)),
        ("Right stick UP", GamepadFrame(ry=0.8)),
        ("Right stick DOWN", GamepadFrame(ry=-0.8)),
        ("Right stick LEFT", GamepadFrame(rx=-0.8)),
        ("Right stick RIGHT", GamepadFrame(rx=0.8)),
        ("Left trigger", GamepadFrame(lt=1.0)),
        ("Right trigger", GamepadFrame(rt=1.0)),
        *[(f"Button {b}", GamepadFrame(buttons=frozenset({b}))) for b in BUTTON_STEPS],
        ("Neutral", GamepadFrame()),
    ]


# ---------------------------------------------------------------------------- XInput read-back (Windows)
class _Gamepad(ctypes.Structure):
    _fields_ = [("wButtons", ctypes.c_ushort), ("bLeftTrigger", ctypes.c_ubyte), ("bRightTrigger", ctypes.c_ubyte),
                ("sThumbLX", ctypes.c_short), ("sThumbLY", ctypes.c_short),
                ("sThumbRX", ctypes.c_short), ("sThumbRY", ctypes.c_short)]  # fmt: skip


class _State(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_uint), ("Gamepad", _Gamepad)]


class XInputReader:
    def __init__(self) -> None:
        self._dll = ctypes.WinDLL("xinput1_4")
        # XInputGetStateEx (ordinal 100) also reports the GUIDE button; XInputGetState does not.
        try:
            self._get = self._dll[100]
            self.reports_guide = True
        except (AttributeError, OSError):
            self._get = self._dll.XInputGetState
            self.reports_guide = False

    def read(self, index: int) -> dict | None:
        st = _State()
        if self._get(index, ctypes.byref(st)) != 0:
            return None
        g = st.Gamepad
        return {"buttons": g.wButtons, "lt": g.bLeftTrigger, "rt": g.bRightTrigger,
                "lx": g.sThumbLX / 32767, "ly": g.sThumbLY / 32767, "rx": g.sThumbRX / 32767, "ry": g.sThumbRY / 32767}  # fmt: skip

    def connected(self) -> set[int]:
        return {i for i in range(4) if self.read(i) is not None}


def check_readback(frame: GamepadFrame, s: dict) -> str | None:
    """Return a problem string, or None when the read-back state matches the commanded frame."""
    for axis in ("lx", "ly", "rx", "ry"):
        want = getattr(frame, axis)
        got = s[axis]
        if want and (got * want <= 0 or abs(got) < 0.6 * abs(want)):
            return f"{axis}: commanded {want:+.2f}, read {got:+.2f}"
        if not want and abs(got) > 0.15:
            return f"{axis}: commanded 0, read {got:+.2f}"
    for trig in ("lt", "rt"):
        want = getattr(frame, trig)
        if want and s[trig] < 200:
            return f"{trig}: commanded {want:.2f}, read {s[trig]}"
        if not want and s[trig] > 20:
            return f"{trig}: commanded 0, read {s[trig]}"
    want_bits = sum(XINPUT_BITS[b] for b in frame.buttons)
    if s["buttons"] != want_bits:
        return f"buttons: commanded 0x{want_bits:04x}, read 0x{s['buttons']:04x}"
    return None


# ---------------------------------------------------------------------------- commands
def cmd_padtest(a: argparse.Namespace) -> int:
    """Player-sourced test pattern through the Governor. Watch it in joy.cpl, or use --readback."""
    from .control.adapters import make_adapter
    from .control.governor import Governor
    from .control.intent_log import IntentLog, load_or_create_log_key
    from .control.motor import MotorModel
    from .control.policy import GovernorConfig
    from .control.safety import KillSwitch

    s = load_settings(a.config, a.profile)
    output = a.output or s.output
    reader = XInputReader() if a.readback else None
    if a.readback and output != "x360":
        print("--readback needs --output x360 (XInput cannot read a DS4).")
        return 2
    before = reader.connected() if reader else set()
    adapter = make_adapter(output, invert_y=s.invert_y)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = IntentLog(Path(s.log_dir) / f"padtest-{stamp}.jsonl")
    kill = KillSwitch(s.stop_file)
    kill.start_hotkeys()
    gov = Governor(GovernorConfig(require_focus=False), MotorModel(s.motor), adapter, log, kill, lambda: True,
                   seal_key=load_or_create_log_key(), session_info={"purpose": "padtest"})  # fmt: skip
    index = None
    results: list[dict] = []
    seq = 0
    try:
        if reader:
            time.sleep(1.0)  # let the virtual pad enumerate
            new = sorted(reader.connected() - before)
            if not new:
                print("Read-back: no new XInput device appeared after creating the virtual pad.")
                return 3
            index = new[0]
            print(f"Read-back on XInput user index {index} (pre-existing devices: {sorted(before) or 'none'})")
        for label, frame in padtest_steps():
            end = time.monotonic() + a.hold
            while time.monotonic() < end and not kill.tripped:
                seq += 1
                pkt = IntentPacket(seq=seq, source=Source.PLAYER, created_at=time.monotonic(), ttl_ms=200,
                                   frames=(frame,), note=f"padtest: {label}")  # fmt: skip
                gov.handle("intent", pkt.to_dict())
                for _ in range(6):
                    gov.tick()
                    time.sleep(1 / 120)
            if kill.tripped:
                print("Kill switch tripped; stopping.")
                halt = {"step": f"HALT during {label}"}
                if reader:
                    for _ in range(12):  # keep ticking: a halted Governor must hold the pad at neutral
                        gov.tick()
                        time.sleep(1 / 120)
                    state = reader.read(index)
                    problem = "device disconnected" if state is None else check_readback(GamepadFrame(), state)
                    halt |= {"read": state, "ok": problem is None, "problem": problem}
                    print(f"  {'pad after halt':22} " + ("NEUTRAL" if problem is None else f"NOT NEUTRAL {problem}"))
                results.append(halt)
                break
            row = {"step": label}
            if reader:
                state = reader.read(index)
                problem = "device disconnected" if state is None else check_readback(frame, state)
                row |= {"read": state, "ok": problem is None, "problem": problem}
            results.append(row)
            print(f"  {label:22} " + ("" if not reader else ("OK" if row["ok"] else f"MISMATCH {row['problem']}")))
    finally:
        gov.close()
    if a.report:
        Path(a.report).write_text(json.dumps({"output": output, "xinput_index": index, "log": str(log.path),
                                              "steps": results}, indent=2), encoding="utf-8")  # fmt: skip
    print(f"Intent log: {log.path}")
    if reader:
        bad = [r for r in results if not r["ok"]]
        print(f"Read-back: {len(results) - len(bad)}/{len(results)} steps matched")
        if kill.tripped:
            return 4 if not bad else 1  # 4: halted cleanly with neutral output; 1: a mismatch
        return 1 if bad else 0
    return 0


def cmd_verify_log(a: argparse.Namespace) -> int:
    from .control.intent_log import load_or_create_log_key, verify_log, verify_seal

    ok, n, _, problem = verify_log(a.path)
    print(f"chain: {'OK' if ok else 'BROKEN'} ({n} records){'' if ok else ' - ' + problem}")
    if not ok:
        return 1
    sok, sproblem = verify_seal(a.path, load_or_create_log_key())
    print(f"seal:  {'OK' if sok else 'NOT VERIFIED'}{'' if sok else ' - ' + sproblem}")
    return 0 if sok else 1


def cmd_stop(a: argparse.Namespace) -> int:
    s = load_settings(a.config, a.profile)
    Path(s.stop_file).parent.mkdir(parents=True, exist_ok=True)
    Path(s.stop_file).touch()
    print(f"Created {s.stop_file}: the Governor halts within one tick. Delete it before the next session.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aether", description="Æther platform. The companion is PR-REX.")
    ap.add_argument("--config", help="settings YAML (default: aether/control/default.yaml)")
    ap.add_argument("--profile", help="profile YAML (configuration/profiles/)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pt = sub.add_parser("padtest")
    pt.add_argument("--output", choices=["x360", "ds4", "dryrun"])
    pt.add_argument("--hold", type=float, default=1.5, help="seconds per step")
    pt.add_argument("--readback", action="store_true", help="verify each step over XInput (Windows, x360)")
    pt.add_argument("--report", help="write a JSON report of the run")
    pt.set_defaults(fn=cmd_padtest)
    v = sub.add_parser("verify-log")
    v.add_argument("path")
    v.set_defaults(fn=cmd_verify_log)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
