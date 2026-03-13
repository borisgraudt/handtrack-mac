"""
utils/smoother.py
OneEuro Filter — the gold standard for low-latency cursor smoothing.
Paper: http://cristal.univ-lille.fr/~casiez/1euro/
"""

import time
import math


class _LowPassFilter:
    def __init__(self):
        self._y    = None
        self._a    = None

    def filter(self, x, alpha):
        if self._y is None:
            self._y = x
        self._y = alpha * x + (1.0 - alpha) * self._y
        return self._y

    @property
    def last_value(self):
        return self._y


class OneEuroFilter:
    """
    Parameters
    ----------
    min_cutoff : float
        Lower  → smoother at rest, but more lag. Try 0.5–2.0.
    beta       : float
        Higher → less lag on fast motion. Try 0.0–1.0.
    d_cutoff   : float
        Cutoff for derivative. Usually leave at 1.0.
    """

    def __init__(self, min_cutoff=1.0, beta=0.1, d_cutoff=1.0):
        self._min_cutoff = min_cutoff
        self._beta       = beta
        self._d_cutoff   = d_cutoff
        self._x_filter   = _LowPassFilter()
        self._dx_filter  = _LowPassFilter()
        self._last_time  = None

    def filter(self, x: float, timestamp: float | None = None) -> float:
        now = timestamp if timestamp is not None else time.monotonic()

        if self._last_time is None:
            dt = 0.016          # assume 60fps on first frame
        else:
            dt = now - self._last_time
            dt = max(dt, 1e-6)

        self._last_time = now

        # Derivative
        dx_raw = 0.0 if self._x_filter.last_value is None \
                     else (x - self._x_filter.last_value) / dt

        alpha_d = self._alpha(dt, self._d_cutoff)
        dx = self._dx_filter.filter(dx_raw, alpha_d)

        # Adaptive cutoff
        cutoff = self._min_cutoff + self._beta * abs(dx)
        alpha  = self._alpha(dt, cutoff)

        return self._x_filter.filter(x, alpha)

    @staticmethod
    def _alpha(dt: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
