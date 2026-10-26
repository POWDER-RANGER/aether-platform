"""Keyboard and mouse output: a second peripheral path behind the Governor.

The Governor's normalized action is the GamepadFrame. This adapter turns each frame it is given into
key and mouse-button state plus relative mouse motion, using an explicit mapping, and injects it with
Windows SendInput (scancodes, no DLL injection). It sits at the same boundary as the virtual-pad adapters,
so the kill switch, policy, delegation, watchdog and neutral-on-stop rules apply unchanged: a neutral
frame releases every key and button.

Safety specific to this path:
  - focus gate: when the target window is not in front, every key and button is released and nothing is
    sent, so keystrokes never land in another application;
  - release before press on every update, and everything released on close;
  - Windows/menu keys cannot be mapped;
  - every injected event carries INJECT_TAG in dwExtraInfo so a later input hook can tell it apart.

Known limit (DECISIONS D-021): the player keyboard source polls GetAsyncKeyState and cannot tell injected
keys from the player's, so player keyboard input must not run together with this output.
"""

from __future__ import annotations

import ctypes
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

from .adapters import OutputAdapter
from .intent import BUTTONS, GamepadFrame
from .player import KEY_TARGETS, VK_NAMES

INJECT_TAG = 0xAE7E
MOUSE_BUTTONS = ("MOUSE_LEFT", "MOUSE_RIGHT", "MOUSE_MIDDLE")
MOUSE_AXES = ("MOUSE_X", "MOUSE_Y")
STICK_AXES = ("LX", "LY", "RX", "RY")
BLOCKED_VK = {0x5B, 0x5C, 0x5D}  # left/right Windows key, menu key
EXTENDED_VK = {0x25, 0x26, 0x27, 0x28}  # arrow keys need KEYEVENTF_EXTENDEDKEY

# Example mapping: a common action-game layout. Game Packs or profiles override it (settings key `kbm`).
DEFAULT_KBM_MAP: dict[str, str] = {
    "LY+": "W", "LY-": "S", "LX-": "A", "LX+": "D",
    "RX": "MOUSE_X", "RY": "MOUSE_Y",
    "LT": "MOUSE_RIGHT", "RT": "MOUSE_LEFT",
    "SOUTH": "SPACE", "EAST": "C", "WEST": "E", "NORTH": "R",
    "LEFT_SHOULDER": "Q", "RIGHT_SHOULDER": "F", "LEFT_THUMB": "SHIFT", "RIGHT_THUMB": "V",
    "DPAD_UP": "1", "DPAD_DOWN": "2", "DPAD_LEFT": "3", "DPAD_RIGHT": "4",
    "START": "P", "BACK": "M",
}  # fmt: skip


@dataclass(frozen=True)
class KbmMapping:
    keys: tuple[tuple[str, int], ...]  # (control target, virtual-key code)
    buttons: tuple[tuple[str, str], ...]  # (control target, MOUSE_LEFT|MOUSE_RIGHT|MOUSE_MIDDLE)
    axes: tuple[tuple[str, str], ...]  # (LX|LY|RX|RY, MOUSE_X|MOUSE_Y)
    threshold: float = 0.5  # stick/trigger value that counts as a key press
    mouse_px_per_s: float = 900.0  # mouse speed at full stick deflection

    @staticmethod
    def from_dict(d: dict[str, str] | None = None, threshold: float = 0.5, mouse_px_per_s: float = 900.0) -> KbmMapping:
        d = dict(DEFAULT_KBM_MAP if d is None else d)
        if not 0.0 < threshold <= 1.0:
            raise ValueError("kbm threshold must be in (0, 1]")
        if not 0.0 < mouse_px_per_s <= 10000.0:
            raise ValueError("kbm mouse_px_per_s must be in (0, 10000]")
        keys, buttons, axes = [], [], []
        for target, out in d.items():
            target, out = str(target).upper(), str(out).upper()
            if target in STICK_AXES:
                if out not in MOUSE_AXES:
                    raise ValueError(f"{target} maps to a whole axis; use MOUSE_X or MOUSE_Y, not {out}")
                axes.append((target, out))
                continue
            if target not in BUTTONS and target not in KEY_TARGETS:
                raise ValueError(f"unknown control target: {target}")
            if out in MOUSE_BUTTONS:
                buttons.append((target, out))
            elif out in VK_NAMES:
                vk = VK_NAMES[out]
                if vk in BLOCKED_VK:
                    raise ValueError(f"key {out} cannot be mapped")
                keys.append((target, vk))
            else:
                raise ValueError(f"unknown key or mouse output for {target}: {out}")
        return KbmMapping(tuple(keys), tuple(buttons), tuple(axes), threshold, mouse_px_per_s)


@dataclass(frozen=True)
class KbmState:
    keys: frozenset[int]
    buttons: frozenset[str]
    dx: int
    dy: int


def _active(frame: GamepadFrame, target: str, threshold: float) -> bool:
    if target in ("LT", "RT"):
        return getattr(frame, target.lower()) >= threshold
    if target in KEY_TARGETS:
        v = getattr(frame, target[:2].lower())
        return v >= threshold if target[2] == "+" else v <= -threshold
    return target in frame.buttons


class KbmPlanner:
    """Pure translation from frames to key/button state and integer mouse deltas (sub-pixel remainder kept)."""

    def __init__(self, mapping: KbmMapping):
        self.m = mapping
        self._acc = {"MOUSE_X": 0.0, "MOUSE_Y": 0.0}

    def reset(self) -> None:
        self._acc = {"MOUSE_X": 0.0, "MOUSE_Y": 0.0}

    def plan(self, frame: GamepadFrame, dt: float) -> KbmState:
        keys = frozenset(vk for t, vk in self.m.keys if _active(frame, t, self.m.threshold))
        buttons = frozenset(b for t, b in self.m.buttons if _active(frame, t, self.m.threshold))
        for axis, out in self.m.axes:
            v = getattr(frame, axis.lower())
            if axis in ("LY", "RY"):
                v = -v  # stick up is +; screen y grows downward
            self._acc[out] += v * self.m.mouse_px_per_s * dt
        dx, dy = int(self._acc["MOUSE_X"]), int(self._acc["MOUSE_Y"])
        self._acc["MOUSE_X"] -= dx
        self._acc["MOUSE_Y"] -= dy
        return KbmState(keys, buttons, dx, dy)


class RecordingBackend:
    """Test backend: records the injected events in order."""

    def __init__(self) -> None:
        self.events: list[tuple] = []

    def key(self, vk: int, down: bool) -> None:
        self.events.append(("key", vk, down))

    def button(self, name: str, down: bool) -> None:
        self.events.append(("button", name, down))

    def move(self, dx: int, dy: int) -> None:
        self.events.append(("move", dx, dy))


class SendInputBackend:
    """Windows SendInput with scancodes. Every event is tagged with INJECT_TAG."""

    _BTN = {"MOUSE_LEFT": (0x0002, 0x0004), "MOUSE_RIGHT": (0x0008, 0x0010), "MOUSE_MIDDLE": (0x0020, 0x0040)}

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("keyboard/mouse output is Windows-only (use RecordingBackend in tests)")
        import ctypes.wintypes as w

        ulong_ptr = ctypes.c_size_t

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", w.DWORD), ("dwFlags", w.DWORD),
                        ("time", w.DWORD), ("dwExtraInfo", ulong_ptr)]  # fmt: skip

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD), ("time", w.DWORD),
                        ("dwExtraInfo", ulong_ptr)]  # fmt: skip

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]

        class _U(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", w.DWORD), ("u", _U)]

        self._INPUT, self._MOUSEINPUT, self._KEYBDINPUT = INPUT, MOUSEINPUT, KEYBDINPUT
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.SendInput.argtypes = (w.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        self._user32.SendInput.restype = w.UINT
        self._user32.MapVirtualKeyW.argtypes = (w.UINT, w.UINT)
        self._user32.MapVirtualKeyW.restype = w.UINT

    def _send(self, inp) -> None:
        if self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp)) != 1:
            raise OSError(ctypes.get_last_error(), "SendInput was blocked")

    def key(self, vk: int, down: bool) -> None:
        scan = self._user32.MapVirtualKeyW(vk, 0)
        flags = 0x0008 | (0 if down else 0x0002) | (0x0001 if vk in EXTENDED_VK else 0)
        ki = self._KEYBDINPUT(0, scan, flags, 0, INJECT_TAG)
        inp = self._INPUT(1)
        inp.u.ki = ki
        self._send(inp)

    def button(self, name: str, down: bool) -> None:
        flag = self._BTN[name][0 if down else 1]
        inp = self._INPUT(0)
        inp.u.mi = self._MOUSEINPUT(0, 0, 0, flag, 0, INJECT_TAG)
        self._send(inp)

    def move(self, dx: int, dy: int) -> None:
        inp = self._INPUT(0)
        inp.u.mi = self._MOUSEINPUT(dx, dy, 0, 0x0001, 0, INJECT_TAG)
        self._send(inp)


class KeyboardMouseAdapter(OutputAdapter):
    name = "kbm"

    def __init__(
        self,
        mapping: KbmMapping | None = None,
        backend=None,
        focus: Callable[[], bool] | None = None,
        clock: Callable[[], float] = time.monotonic,
        max_dt: float = 0.05,
    ):
        self.mapping = mapping or KbmMapping.from_dict()
        self.planner = KbmPlanner(self.mapping)
        self.backend = backend if backend is not None else SendInputBackend()
        self.focus = focus
        self.clock = clock
        self.max_dt = max_dt
        self.keys_down: set[int] = set()
        self.buttons_down: set[str] = set()
        self._last: float | None = None
        self.stats = {"focus_releases": 0, "moves": 0}

    def release_all(self) -> None:
        for vk in sorted(self.keys_down):
            self.backend.key(vk, False)
        for b in sorted(self.buttons_down):
            self.backend.button(b, False)
        self.keys_down.clear()
        self.buttons_down.clear()
        self.planner.reset()

    def apply(self, frame: GamepadFrame) -> None:
        now = self.clock()
        dt = 0.0 if self._last is None else min(max(now - self._last, 0.0), self.max_dt)
        self._last = now
        if self.focus is not None and not self.focus():
            if self.keys_down or self.buttons_down:
                self.stats["focus_releases"] += 1
            self.release_all()
            return
        st = self.planner.plan(frame, dt)
        for vk in sorted(self.keys_down - st.keys):  # release before press
            self.backend.key(vk, False)
        for b in sorted(self.buttons_down - st.buttons):
            self.backend.button(b, False)
        for vk in sorted(st.keys - self.keys_down):
            self.backend.key(vk, True)
        for b in sorted(st.buttons - self.buttons_down):
            self.backend.button(b, True)
        self.keys_down, self.buttons_down = set(st.keys), set(st.buttons)
        if st.dx or st.dy:
            self.backend.move(st.dx, st.dy)
            self.stats["moves"] += 1

    def neutral(self) -> None:
        self.release_all()

    def close(self) -> None:
        self.release_all()
