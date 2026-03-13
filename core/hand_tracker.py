# core/hand_tracker.py

import cv2
import numpy as np
from config import CONFIG

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
    NEW_API = True
except (ImportError, AttributeError):
    NEW_API = False

if not NEW_API:
    import mediapipe as mp


class HandTracker:
    def __init__(self):
        if NEW_API:
            self._init_new_api()
        else:
            self._init_old_api()

    def _init_new_api(self):
        import urllib.request, os
        model_path = "/tmp/hand_landmarker.task"
        if not os.path.exists(model_path):
            print("   Downloading hand landmark model (~9MB)...")
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                model_path
            )
            print("   Model downloaded.")

        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from mediapipe.tasks import python as mp_python

        options = HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.IMAGE,
            num_hands=CONFIG["max_hands"],
            min_hand_detection_confidence=CONFIG["detection_confidence"],
            min_hand_presence_confidence=CONFIG["detection_confidence"],
            min_tracking_confidence=CONFIG["tracking_confidence"],
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._use_new = True

    def _init_old_api(self):
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=CONFIG["max_hands"],
            min_detection_confidence=CONFIG["detection_confidence"],
            min_tracking_confidence=CONFIG["tracking_confidence"],
        )
        self._use_new = False

    def process(self, frame_bgr) -> list | None:
        if self._use_new:
            return self._process_new(frame_bgr)
        else:
            return self._process_old(frame_bgr)

    def _process_new(self, frame_bgr) -> list | None:
        import mediapipe as mp
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.hand_landmarks:
            return None
        hand = result.hand_landmarks[0]
        return [(lm.x, lm.y, lm.z) for lm in hand]

    def _process_old(self, frame_bgr) -> list | None:
        rgb = frame_bgr[:, :, ::-1]
        result = self._hands.process(rgb)
        if not result.multi_hand_landmarks:
            return None
        hand = result.multi_hand_landmarks[0]
        return [(lm.x, lm.y, lm.z) for lm in hand.landmark]

    def close(self):
        if self._use_new:
            self._landmarker.close()
        else:
            self._hands.close()