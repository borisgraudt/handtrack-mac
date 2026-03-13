"""
overlay/renderer.py
Draws the hand skeleton, landmark dots, and pinch indicator
on a tkinter Canvas in a Vision Pro / Apple aesthetic.

Visual language:
  - Thin white semi-transparent skeleton lines
  - Small filled white dots at each joint
  - A glowing ring between thumb tip and index tip
    grey when idle, white + larger when pinching
  - A subtle label showing gesture state
"""

import math
import tkinter as tk
from config import CONFIG, HAND_CONNECTIONS


# Joints that get slightly larger dots (fingertips)
FINGERTIPS = {4, 8, 12, 16, 20}

# Skeleton line widths per segment type
_PALM_PAIRS = {(5, 9), (9, 13), (13, 17)}


class HandRenderer:
    def __init__(self):
        self._canvas  = None
        self._sw      = 1
        self._sh      = 1
        self._items   = []      # canvas item IDs to delete each frame

        # Cached config values
        self._dot_r         = CONFIG["dot_radius"]
        self._dot_color     = CONFIG["dot_color"]
        self._skel_color    = CONFIG["skeleton_color"]
        self._ring_idle     = CONFIG["pinch_ring_color_idle"]
        self._ring_active   = CONFIG["pinch_ring_color_active"]
        self._ring_r        = CONFIG["pinch_ring_radius"]

    # ── Setup ─────────────────────────────────────────────────────────────
    def setup(self, canvas: tk.Canvas, sw: int, sh: int):
        self._canvas = canvas
        self._sw     = sw
        self._sh     = sh

    # ── Main draw call ────────────────────────────────────────────────────
    def draw(self, landmarks, gesture):
        c = self._canvas
        # Clear previous frame
        for item in self._items:
            c.delete(item)
        self._items.clear()

        if landmarks is None or gesture is None or gesture.kind == "NONE":
            return

        pts = self._to_screen(landmarks)
        pinching = gesture.kind in ("PINCH_START", "PINCH_HOLD", "DRAG",
                                    "DOUBLE_TAP")

        self._draw_skeleton(pts)
        self._draw_dots(pts)
        self._draw_pinch_ring(pts, pinching, gesture)
        self._draw_gesture_label(gesture)

    # ── Skeleton lines ────────────────────────────────────────────────────
    def _draw_skeleton(self, pts):
        c = self._canvas
        for a, b in HAND_CONNECTIONS:
            x0, y0 = pts[a]
            x1, y1 = pts[b]
            pair = (min(a, b), max(a, b))
            width = 1 if pair in _PALM_PAIRS else 1.5
            item = c.create_line(
                x0, y0, x1, y1,
                fill=self._skel_color,
                width=width,
                smooth=True,
                capstyle=tk.ROUND,
            )
            # Simulate transparency via stipple pattern
            c.itemconfig(item, stipple="gray50")
            self._items.append(item)

    # ── Joint dots ────────────────────────────────────────────────────────
    def _draw_dots(self, pts):
        c = self._canvas
        for i, (x, y) in enumerate(pts):
            r = self._dot_r + (2 if i in FINGERTIPS else 0)
            item = c.create_oval(
                x - r, y - r, x + r, y + r,
                fill=self._dot_color,
                outline="",
            )
            self._items.append(item)


    # ── Pinch ring between thumb tip and index tip ────────────────────────
    def _draw_pinch_ring(self, pts, pinching: bool, gesture):
        c = self._canvas
        tx, ty = pts[4]   # thumb tip
        ix, iy = pts[8]   # index tip

        # Midpoint
        mx = (tx + ix) / 2
        my = (ty + iy) / 2

        color = self._ring_active if pinching else self._ring_idle
        r     = self._ring_r + (6 if pinching else 0)

        # Outer glow (simulated with a larger, stippled circle)
        if pinching:
            glow_r = r + 10
            glow = c.create_oval(
                mx - glow_r, my - glow_r,
                mx + glow_r, my + glow_r,
                fill="", outline="white", width=2,
            )
            c.itemconfig(glow, stipple="gray25")
            self._items.append(glow)

        # Main ring
        ring = c.create_oval(
            mx - r, my - r, mx + r, my + r,
            fill="", outline=color, width=2,
        )
        self._items.append(ring)

        # Line connecting thumb tip to index tip
        line = c.create_line(
            tx, ty, ix, iy,
            fill=color, width=1, dash=(4, 6),
        )
        self._items.append(line)

    # ── Gesture state label ───────────────────────────────────────────────
    def _draw_gesture_label(self, gesture):
        c = self._canvas
        labels = {
            "MOVE":        "",
            "PINCH_START": "●  pinch",
            "PINCH_HOLD":  "●  hold",
            "DRAG":        "⟡  drag",
            "PINCH_END":   "",
            "DOUBLE_TAP":  "◎  open",
            "NONE":        "",
        }
        text = labels.get(gesture.kind, "")
        if not text:
            return

        item = c.create_text(
            self._sw // 2, self._sh - 60,
            text=text,
            fill="white",
            font=("SF Pro Display", 16, "normal"),
            anchor="center",
        )
        self._items.append(item)

    # ── Coordinate conversion ─────────────────────────────────────────────
    def _to_screen(self, landmarks) -> list:
        """Convert normalised [0..1] landmarks to screen pixel coords."""
        margin = CONFIG["edge_margin"]
        scale  = 1.0 / (1.0 - 2 * margin)
        result = []
        for (nx, ny, _) in landmarks:
            sx = int(((nx - margin) * scale) * self._sw)
            sy = int(((ny - margin) * scale) * self._sh)
            result.append((sx, sy))
        return result
