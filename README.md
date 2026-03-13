# HandTrack Mac 🖐

Vision Pro-style hand control for macOS via webcam + MediaPipe.

- Move cursor with your index fingertip
- **Pinch** (thumb + index) → click / start drag
- **Hold pinch + move** → drag files/windows
- **Double pinch** → double-click (open file/folder)
- **Escape** → quit overlay

---

## Setup

### 1. Install Python 3.11+
```bash
brew install python@3.11
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Grant permissions (macOS requires this)

**Camera:** System Settings → Privacy & Security → Camera → allow Terminal / your IDE

**Accessibility:** System Settings → Privacy & Security → Accessibility → add Terminal (or Python)
This is required for cursor control via Quartz.

### 4. Run
```bash
python3 main.py
```

Press **Escape** to quit the overlay.

---

## Tuning

Edit `config.py` to adjust:

| Parameter | Effect |
|---|---|
| `pinch_threshold` | How close fingers need to be to trigger pinch (lower = harder) |
| `double_tap_ms` | Max gap between two pinches for double-click |
| `one_euro_beta` | Higher = less lag on fast movement |
| `one_euro_min_cutoff` | Lower = smoother at rest |
| `edge_margin` | Dead zone at camera edges (0.15 = 15%) |

---

## Architecture

```
Webcam Thread → frame_queue → Processing Thread → landmark_queue → UI Thread
                                     ↓
                              CursorController (Quartz)
```

Three parallel threads communicate via `queue.Queue` — no blocking, no dropped frames.
