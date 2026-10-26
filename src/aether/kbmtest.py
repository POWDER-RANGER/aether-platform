"""Keyboard/mouse read-back test (Windows): `python -m aether kbmtest`.

Opens its own window, keeps the cursor inside it, and drives every mapped control through the Governor and
the keyboard/mouse adapter. Each step is read back with GetAsyncKeyState (keys, mouse buttons) and
GetCursorPos (motion). Also checks that losing focus releases everything and blocks output, and that a
kill-switch halt leaves every key and button released.
"""

from __future__ import annotations

import ctypes
import json
import time
from pathlib import Path

from .control.intent import GamepadFrame, IntentPacket, Source
from .control.kbm import KbmMapping, KeyboardMouseAdapter
from .control.settings import load_settings

MOUSE_VK = {"MOUSE_LEFT": 0x01, "MOUSE_RIGHT": 0x02, "MOUSE_MIDDLE": 0x04}


def frame_for(target: str, sign: float = 1.0) -> GamepadFrame:
    if target in ("LT", "RT"):
        return GamepadFrame(**{target.lower(): 1.0})
    if target in ("LX", "LY", "RX", "RY"):
        return GamepadFrame(**{target.lower(): 0.9 * sign})
    if len(target) == 3 and target[2] in "+-" and target[:2] in ("LX", "LY", "RX", "RY"):
        return GamepadFrame(**{target[:2].lower(): 0.9 if target[2] == "+" else -0.9})
    return GamepadFrame(buttons=frozenset({target}))


def build_steps(m: KbmMapping) -> list[dict]:
    steps = []
    by_target: dict[str, dict] = {}
    for t, vk in m.keys:
        by_target.setdefault(t, {"keys": set(), "buttons": set()})["keys"].add(vk)
    for t, b in m.buttons:
        by_target.setdefault(t, {"keys": set(), "buttons": set()})["buttons"].add(b)
    for t, exp in by_target.items():
        steps.append({"label": t, "frame": frame_for(t), "keys": exp["keys"], "buttons": exp["buttons"], "move": None})
    for axis, out in m.axes:
        for sign in (1.0, -1.0):
            want = sign if axis in ("LX", "RX") else -sign  # stick up moves the cursor up (screen y decreases)
            steps.append({"label": f"{axis}{'+' if sign > 0 else '-'} -> {out}", "frame": frame_for(axis, sign),
                          "keys": set(), "buttons": set(), "move": (out, want)})  # fmt: skip
    steps.append({"label": "Neutral", "frame": GamepadFrame(), "keys": set(), "buttons": set(), "move": None})
    return steps


def run(a) -> int:
    import tkinter as tk

    from .control.governor import Governor
    from .control.intent_log import IntentLog, load_or_create_log_key
    from .control.motor import MotorModel
    from .control.policy import GovernorConfig
    from .control.safety import KillSwitch

    s = load_settings(a.config, a.profile)
    k = s.kbm or {}
    mapping = KbmMapping.from_dict(
        k.get("map"), k.get("threshold", 0.5), a.mouse_px_per_s or k.get("mouse_px_per_s", 900.0)
    )
    user32 = ctypes.WinDLL("user32")

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    root = tk.Tk()
    root.title("Aether keyboard/mouse test")
    root.geometry("640x420+240+200")
    root.attributes("-topmost", True)
    tk.Label(root, text="Æther keyboard/mouse test. Hands off keyboard and mouse until it closes.", pady=20).pack()
    root.update()
    root.focus_force()
    root.update()
    hwnd = user32.GetAncestor(root.winfo_id(), 2)
    user32.SetForegroundWindow(hwnd)
    root.update()

    def focused() -> bool:
        return user32.GetForegroundWindow() == hwnd

    def center() -> None:
        user32.SetCursorPos(root.winfo_rootx() + 320, root.winfo_rooty() + 210)

    def cursor() -> tuple[int, int]:
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def down(vk: int) -> bool:
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

    if not focused():
        print("The test window could not take focus; nothing was sent.")
        root.destroy()
        return 3
    swapped = bool(user32.GetSystemMetrics(23))
    all_keys = {vk for _, vk in mapping.keys}
    all_buttons = {b for _, b in mapping.buttons}

    def check(step: dict, moved: tuple[int, int]) -> str | None:
        for vk in all_keys:
            if down(vk) != (vk in step["keys"]):
                return (
                    f"key 0x{vk:02x} {'down' if down(vk) else 'up'}, expected {'down' if vk in step['keys'] else 'up'}"
                )
        for b in all_buttons:
            vk = MOUSE_VK[b]
            if swapped and b in ("MOUSE_LEFT", "MOUSE_RIGHT"):
                vk = MOUSE_VK["MOUSE_RIGHT" if b == "MOUSE_LEFT" else "MOUSE_LEFT"]
            if down(vk) != (b in step["buttons"]):
                return f"{b} {'down' if down(vk) else 'up'}, expected {'down' if b in step['buttons'] else 'up'}"
        if step["move"]:
            out, want = step["move"]
            d = moved[0] if out == "MOUSE_X" else moved[1]
            if d * want <= 0 or abs(d) < 10:
                return f"{out} moved {d:+d}, expected sign {want:+.0f}"
        elif abs(moved[0]) > 2 or abs(moved[1]) > 2:
            return f"cursor moved {moved} on a step with no mouse motion"
        return None

    adapter = KeyboardMouseAdapter(mapping, focus=focused)
    log = IntentLog(Path(s.log_dir) / f"kbmtest-{time.strftime('%Y%m%d-%H%M%S')}.jsonl")
    kill = KillSwitch(s.stop_file)
    kill.start_hotkeys()
    gov = Governor(GovernorConfig(require_focus=False), MotorModel(s.motor), adapter, log, kill, focused,
                   seal_key=load_or_create_log_key(), session_info={"purpose": "kbmtest"})  # fmt: skip
    seq = 0
    results: list[dict] = []

    def hold(frame: GamepadFrame, seconds: float, label: str) -> None:
        nonlocal seq
        end = time.monotonic() + seconds
        while time.monotonic() < end and not kill.tripped:
            seq += 1
            pkt = IntentPacket(seq=seq, source=Source.PLAYER, created_at=time.monotonic(), ttl_ms=200,
                               frames=(frame,), note=f"kbmtest: {label}")  # fmt: skip
            gov.handle("intent", pkt.to_dict())
            for _ in range(6):
                gov.tick()
                root.update()
                time.sleep(1 / 120)

    try:
        steps = build_steps(mapping)
        for step in steps:
            center()
            root.update()
            hold(GamepadFrame(), 0.15, "settle")
            x0, y0 = cursor()
            hold(step["frame"], a.hold, step["label"])
            if kill.tripped:
                break
            x1, y1 = cursor()
            problem = check(step, (x1 - x0, y1 - y0))
            results.append(
                {"step": step["label"], "ok": problem is None, "problem": problem, "moved": [x1 - x0, y1 - y0]}
            )
            print(f"  {step['label']:26} " + ("OK" if problem is None else f"MISMATCH {problem}"))
        if not kill.tripped and a.focus_test:
            first = steps[0]
            center()
            hold(first["frame"], a.hold, "focus-loss: hold")
            held = all(down(vk) for vk in first["keys"])
            root.iconify()
            root.update()
            time.sleep(0.2)
            hold(first["frame"], a.hold, "focus-loss: unfocused")
            released = not any(down(vk) for vk in all_keys)
            problem = None if (held and released) else f"held={held} released_after_focus_loss={released}"
            results.append({"step": "focus loss releases keys", "ok": problem is None, "problem": problem})
            print(f"  {'focus loss releases keys':26} " + ("OK" if problem is None else f"MISMATCH {problem}"))
            root.deiconify()
            root.update()
        if kill.tripped:
            print("Kill switch tripped; stopping.")
            for _ in range(12):
                gov.tick()
                root.update()
                time.sleep(1 / 120)
            stuck = [f"0x{vk:02x}" for vk in all_keys if down(vk)]
            ok = not stuck
            results.append({"step": "HALT", "ok": ok, "problem": None if ok else f"stuck keys {stuck}"})
            print(f"  {'after halt':26} " + ("ALL RELEASED" if ok else f"STUCK {stuck}"))
    finally:
        gov.close()
        root.destroy()
    if a.report:
        Path(a.report).write_text(json.dumps({"log": str(log.path), "mouse_px_per_s": mapping.mouse_px_per_s,
                                              "steps": results, "adapter_stats": adapter.stats}, indent=2),
                                  encoding="utf-8")  # fmt: skip
    bad = [r for r in results if not r["ok"]]
    print(f"Intent log: {log.path}")
    print(f"Read-back: {len(results) - len(bad)}/{len(results)} checks matched")
    if kill.tripped:
        return 4 if not bad else 1
    return 1 if bad else 0
