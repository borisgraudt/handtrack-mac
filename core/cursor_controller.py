# core/cursor_controller.py

import math
import time

try:
    from Quartz.CoreGraphics import (
        CGEventCreateMouseEvent,
        CGEventSetIntegerValueField,
        CGEventPost,
        CGPoint,
        kCGEventMouseMoved,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventLeftMouseDragged,
        kCGHIDEventTap,
        kCGMouseEventClickState,
        CGDisplayBounds,
        CGMainDisplayID,
    )
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("⚠️  pyobjc-framework-Quartz not found — cursor control disabled.")
    print("   Install: pip install pyobjc-framework-Quartz")

import subprocess
from config import CONFIG


def _screen_size():
    if QUARTZ_AVAILABLE:
        bounds = CGDisplayBounds(CGMainDisplayID())
        return int(bounds.size.width), int(bounds.size.height)
    # Fallback via system_profiler
    try:
        out = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"], text=True
        )
        for line in out.splitlines():
            if "Resolution" in line:
                parts = line.split()
                w, h = int(parts[1]), int(parts[3])
                return w, h
    except Exception:
        pass
    return 1920, 1080


def _post(event_type, x, y, click_count=1):
    if not QUARTZ_AVAILABLE:
        return
    point = CGPoint(x, y)
    ev = CGEventCreateMouseEvent(None, event_type, point, 0)
    CGEventSetIntegerValueField(ev, kCGMouseEventClickState, click_count)
    CGEventPost(kCGHIDEventTap, ev)


class CursorController:
    def __init__(self):
        self._sw, self._sh = _screen_size()
        self._margin        = CONFIG["edge_margin"]
        self._cur_x         = self._sw / 2
        self._cur_y         = self._sh / 2
        self._mouse_down    = False
        print(f"   Screen: {self._sw}×{self._sh}")

    def handle(self, gesture):
        kind = gesture.kind

        if kind == "NONE":
            return

        sx, sy = self._norm_to_screen(gesture.x, gesture.y)

        if kind == "MOVE":
            self._move(sx, sy)

        elif kind == "PINCH_START":
            self._move(sx, sy)
            self._mouse_down_(sx, sy)

        elif kind == "PINCH_HOLD":
            self._move(sx, sy)

        elif kind == "DRAG":
            self._drag(sx, sy)

        elif kind == "PINCH_END":
            self._mouse_up(sx, sy)

        elif kind == "DOUBLE_TAP":
            self._double_click(sx, sy)


    def _norm_to_screen(self, nx, ny):

        # Map normalised landmark coords (0..1) to screen pixels, 
        # cropping the edge margins so you don't have to move your hand 
        # all the way to the camera border.
        m = self._margin
        # Remap [m, 1-m] → [0, 1] then scale to screen
        cx = (nx - m) / (1 - 2 * m)
        cy = (ny - m) / (1 - 2 * m)
        cx = max(0.0, min(1.0, cx))
        cy = max(0.0, min(1.0, cy))
        return int(cx * self._sw), int(cy * self._sh)

    def _move(self, x, y):
        self._cur_x, self._cur_y = x, y
        _post(kCGEventMouseMoved, x, y)

    def _mouse_down_(self, x, y):
        if not self._mouse_down:
            self._mouse_down = True
            _post(kCGEventLeftMouseDown, x, y)

    def _mouse_up(self, x, y):
        if self._mouse_down:
            self._mouse_down = False
            _post(kCGEventLeftMouseUp, x, y)

    def _drag(self, x, y):
        self._cur_x, self._cur_y = x, y
        _post(kCGEventLeftMouseDragged, x, y)

    def _double_click(self, x, y):
        # Simulate a double-click at position.
        if self._mouse_down:
            _post(kCGEventLeftMouseUp, x, y)
            self._mouse_down = False
        _post(kCGEventLeftMouseDown, x, y, 1)
        _post(kCGEventLeftMouseUp,   x, y, 1)
        time.sleep(0.05)
        _post(kCGEventLeftMouseDown, x, y, 2)
        _post(kCGEventLeftMouseUp,   x, y, 2)
