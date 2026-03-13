# core/gesture_engine.py

import time
import math
from config import CONFIG
from utils.smoother import OneEuroFilter


# Landmark indices
THUMB_TIP  = 4
INDEX_MCP  = 5   # base of index finger — stable cursor anchor (doesn't move when pinching)
INDEX_TIP  = 8
WRIST      = 0
MID_MCP    = 9   # middle finger MCP — used as hand-size reference


class GestureResult:
    __slots__ = ("kind", "x", "y", "pinch_distance", "hand_size")

    def __init__(self, kind, x=0.0, y=0.0, pinch_distance=1.0, hand_size=1.0):
        self.kind           = kind          # str
        self.x              = x             # normalised 0..1
        self.y              = y             # normalised 0..1
        self.pinch_distance = pinch_distance
        self.hand_size      = hand_size


class GestureEngine:
    def __init__(self):
        cfg = CONFIG
        self._smoother_x = OneEuroFilter(
            min_cutoff=cfg["one_euro_min_cutoff"],
            beta=cfg["one_euro_beta"],
            d_cutoff=cfg["one_euro_d_cutoff"],
        )
        self._smoother_y = OneEuroFilter(
            min_cutoff=cfg["one_euro_min_cutoff"],
            beta=cfg["one_euro_beta"],
            d_cutoff=cfg["one_euro_d_cutoff"],
        )

        self._pinching          = False
        self._drag_active       = False
        self._drag_origin_x     = 0.0
        self._drag_origin_y     = 0.0

        self._last_pinch_end    = 0.0   # time of last PINCH_END (for double-tap gap)
        self._double_tap_gap    = cfg["double_tap_ms"] / 1000.0
        self._pinch_threshold   = cfg["pinch_threshold"]
        self._pinch_release     = cfg["pinch_release"]
        self._drag_start_px     = cfg["drag_start_px"]

    # ─────────────────────────────────────────────────────────────────────
    def update(self, landmarks) -> GestureResult | None:
        if landmarks is None:
            self._pinching    = False
            self._drag_active = False
            return GestureResult("NONE")

        # Use INDEX_MCP (knuckle base) as cursor anchor — it barely moves when
        # you curl the finger to pinch, so the cursor stays stable.
        raw_x, raw_y, _ = landmarks[INDEX_MCP]
        sx = self._smoother_x.filter(raw_x)
        sy = self._smoother_y.filter(raw_y)

        hand_size       = self._hand_size(landmarks)
        pinch_dist_raw  = self._distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP])
        pinch_dist_norm = pinch_dist_raw / max(hand_size, 1e-6)

        # ── Pinch state machine ──────────────────────────────────────────
        now = time.time()

        if not self._pinching:
            if pinch_dist_norm < self._pinch_threshold:
                # Double-tap: gap measured from end of previous pinch
                gap = now - self._last_pinch_end
                if gap < self._double_tap_gap:
                    self._pinching     = True
                    self._last_pinch_end = 0.0  # reset so triple-tap doesn't fire
                    return GestureResult("DOUBLE_TAP", sx, sy, pinch_dist_norm, hand_size)

                self._pinching      = True
                self._drag_active   = False
                self._drag_origin_x = sx
                self._drag_origin_y = sy
                return GestureResult("PINCH_START", sx, sy, pinch_dist_norm, hand_size)

            return GestureResult("MOVE", sx, sy, pinch_dist_norm, hand_size)

        else:  # currently pinching
            if pinch_dist_norm > self._pinch_release:
                self._pinching       = False
                self._drag_active    = False
                self._last_pinch_end = now   # record when this pinch ended
                return GestureResult("PINCH_END", sx, sy, pinch_dist_norm, hand_size)

            # Still pinching — detect drag
            dx = abs(sx - self._drag_origin_x)
            dy = abs(sy - self._drag_origin_y)
            moved_px = math.hypot(dx, dy) * 1920   # rough screen-space estimate

            if not self._drag_active and moved_px > self._drag_start_px:
                self._drag_active = True

            kind = "DRAG" if self._drag_active else "PINCH_HOLD"
            return GestureResult(kind, sx, sy, pinch_dist_norm, hand_size)

    @staticmethod
    def _distance(a, b) -> float:
        return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    @staticmethod
    def _hand_size(landmarks) -> float:
        # Wrist --> middle MCP distance as a scale reference.
        w = landmarks[WRIST]
        m = landmarks[MID_MCP]
        return math.sqrt((w[0]-m[0])**2 + (w[1]-m[1])**2)
