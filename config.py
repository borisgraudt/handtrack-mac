# config.py — all tunable parameters in one place

CONFIG = {
    # ── Camera ──────────────────────────────────────────────────────────
    "camera_index": 0,
    "cam_width":    640,
    "cam_height":   480,
    "cam_fps":      30,

    # ── MediaPipe ────────────────────────────────────────────────────────
    "max_hands":              1,      # track one hand for now
    "detection_confidence":   0.75,
    "tracking_confidence":    0.75,

    # ── Gesture thresholds ───────────────────────────────────────────────
    # Pinch: distance between thumb tip (4) and index tip (8)
    # expressed as a fraction of hand "size" (wrist→middle_mcp distance)
    "pinch_threshold":        0.17,   # ≤ this → pinch active
    "pinch_release":          0.24,   # ≥ this → pinch released (hysteresis)

    # Double-tap: two pinches within this many milliseconds
    "double_tap_ms":          380,

    # Drag starts when cursor moves more than N px while pinching
    "drag_start_px":          6,

    # ── Smoothing (OneEuro Filter) ────────────────────────────────────────
    "one_euro_min_cutoff":    1.0,    # lower → smoother but more lag
    "one_euro_beta":          0.1,    # higher → less lag on fast movement
    "one_euro_d_cutoff":      1.0,

    # ── Cursor mapping ────────────────────────────────────────────────────
    # Fraction of camera frame to ignore at each edge (dead zone)
    "edge_margin":            0.15,   # 15% on each side

    # ── Overlay visuals ───────────────────────────────────────────────────
    "overlay_opacity":        0.0,    # window background fully transparent
    "dot_radius":             5,      # landmark dot size (px)
    "dot_color":              "#FFFFFF",
    "skeleton_color":         "#FFFFFF",
    "skeleton_alpha":         0.55,   # simulated via stipple/width
    "pinch_ring_color_idle":  "#888888",
    "pinch_ring_color_active":"#FFFFFF",
    "pinch_ring_radius":      18,
    "font_family":            "SF Pro Display",   # falls back to system font

    # ── Debug ─────────────────────────────────────────────────────────────
    "show_debug_window":      False,  # set True to see raw camera feed
}

# MediaPipe hand skeleton connections (pairs of landmark indices)
HAND_CONNECTIONS = [
    (0, 1),  (1, 2),  (2, 3),  (3, 4),    # thumb
    (0, 5),  (5, 6),  (6, 7),  (7, 8),    # index
    (0, 9),  (9, 10), (10,11), (11,12),   # middle
    (0, 13), (13,14), (14,15), (15,16),   # ring
    (0, 17), (17,18), (18,19), (19,20),   # pinky
    (5, 9),  (9, 13), (13,17),            # palm
]
