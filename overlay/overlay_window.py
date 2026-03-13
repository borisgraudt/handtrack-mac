# overlay/overlay_window.py

import tkinter as tk
import queue
import threading

from overlay.renderer import HandRenderer
from config import CONFIG


class OverlayWindow:
    def __init__(self):
        self._renderer = HandRenderer()

    def start(self, landmark_queue: queue.Queue, stop_event: threading.Event):
        """
        Blocking call — runs tkinter main loop on the calling thread.
        """
        root = tk.Tk()
        root.title("HandTrack")

        # ── Make window fullscreen and transparent ────────────────────────
        root.attributes("-fullscreen", True)
        root.attributes("-topmost",    True)
        root.attributes("-alpha",      0.01)     # nearly invisible window bg
        root.config(bg="black")
        root.overrideredirect(True)               # no title bar

        # On macOS, use the transparent window trick:
        # Set background to a colour and make that colour transparent
        TRANSPARENT_COLOR = "black"
        root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        root.config(bg=TRANSPARENT_COLOR)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")

        canvas = tk.Canvas(
            root,
            width=sw, height=sh,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)

        self._renderer.setup(canvas, sw, sh)

        # ── Poll queue and redraw ─────────────────────────────────────────
        def poll():
            if stop_event.is_set():
                root.destroy()
                return

            try:
                frame, landmarks, gesture = landmark_queue.get_nowait()
                self._renderer.draw(landmarks, gesture)
            except queue.Empty:
                pass

            root.after(16, poll)   # ~60fps

        # Allow quitting with Escape
        root.bind("<Escape>", lambda e: stop_event.set())

        root.after(100, poll)
        root.mainloop()
