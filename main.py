#!/usr/bin/env python3

import threading
import queue
import sys
import time
import tkinter as tk
import cv2

from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine
from core.cursor_controller import CursorController
from overlay.renderer import HandRenderer
from config import CONFIG


def main():
    print("🖐  HandTrack Mac starting...")
    print("   Make sure to grant Camera + Accessibility permissions.")
    print("   Press Escape to quit.\n")

    frame_queue    = queue.Queue(maxsize=2)
    landmark_queue = queue.Queue(maxsize=2)
    stop_event     = threading.Event()

    tracker  = HandTracker()
    gesture  = GestureEngine()
    cursor   = CursorController()

    # ── Thread 1: webcam capture ──────────────────────────────────────────
    def capture_loop():
        cap = cv2.VideoCapture(CONFIG["camera_index"])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CONFIG["cam_width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["cam_height"])
        cap.set(cv2.CAP_PROP_FPS,          CONFIG["cam_fps"])
        if not cap.isOpened():
            print("❌ Could not open camera. Check permissions.")
            stop_event.set()
            return
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            try:
                frame_queue.put_nowait(frame)
            except queue.Full:
                pass
        cap.release()

    # ── Thread 2: MediaPipe processing ───────────────────────────────────
    def processing_loop():
        while not stop_event.is_set():
            try:
                frame = frame_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            landmarks      = tracker.process(frame)
            gesture_result = gesture.update(landmarks)
            if gesture_result:
                cursor.handle(gesture_result)
            try:
                landmark_queue.put_nowait((landmarks, gesture_result))
            except queue.Full:
                pass

    # ── Main thread: tkinter overlay ──────────────────────────────────────
    def build_overlay():
        root = tk.Tk()
        root.title("HandTrack")
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.overrideredirect(True)

        root.wm_attributes("-transparent", True)
        root.config(bg="systemTransparent")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")

        canvas = tk.Canvas(root, width=sw, height=sh,
                           bg="systemTransparent", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        renderer = HandRenderer()
        renderer.setup(canvas, sw, sh)

        def poll():
            if stop_event.is_set():
                root.destroy()
                return
            try:
                landmarks, gest = landmark_queue.get_nowait()
                renderer.draw(landmarks, gest)
            except queue.Empty:
                pass
            root.after(16, poll)

        root.bind("<Escape>", lambda e: stop_event.set())
        root.after(200, poll)
        root.mainloop()

    # Start background threads
    t1 = threading.Thread(target=capture_loop,    daemon=True)
    t2 = threading.Thread(target=processing_loop, daemon=True)
    t1.start()
    t2.start()

    print("   Overlay starting... (Escape to quit)")

    try:
        build_overlay()   # blocks on main thread — required by macOS
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print("\n👋 HandTrack Mac stopped.")


if __name__ == "__main__":
    main()