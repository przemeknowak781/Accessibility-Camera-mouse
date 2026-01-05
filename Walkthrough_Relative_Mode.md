# Relative Movement & Advanced Gestures

I have updated the application to support **Relative Movement** (like a touchpad) and more advanced gesture control.

## New Features

### 1. Relative Movement Mode
- **What:** The cursor now moves based on *how much* you move your hand, not *where* your hand is on camera.
- **Why:** You can control the whole screen with small, comfortable hand movements. No need to reach to the edges of the camera frame.
- **Behavior:**
    - When you show your hand, it "grabs" the cursor.
    - Moving hand moves cursor.
    - If you run out of comfortable space, hide hand (lift finger), move back, and show hand again (clutching).
- **Settings:**
    - `MOVEMENT_MODE = "RELATIVE"` (Default) vs `"ABSOLUTE"`.
    - `REL_SENSITIVITY = 2.0` (Higher = faster cursor).
    - `COAST_WINDOW = 0.4` (Time the cursor keeps moving after you stop/hide hand).

### 2. Advanced Clicks
- **Wink Click:** 
    - **Single Wink:** Triggers a click.
    - **Double Blink:** Ignored (Natural blinking safety).
    - **Settings:** `ENABLE_BLINK_CLICK`, `IGNORE_DOUBLE_BLINK`.
- **Pinch Click:**
    - Pinch Index + Thumb.
    - **Settings:** `ENABLE_PINCH_CLICK` (Can be disabled if you prefer only winking).

## Usage Guide
1.  **Start:** Run `run.bat`.
2.  **Mode:** Press `0` for RELATIVE or `1` for ABSOLUTE.
3.  **Move:** Relax your hand. Move it slightly to push the cursor.
4.  **Click:** Wink one eye OR pinch fingers.

## Toggles (in `src/config.py`)
To customize:
```python
# Feature Toggles
ENABLE_PINCH_CLICK = True   # Set False to disable pinch
ENABLE_BLINK_CLICK = True   # Set False to disable wink
IGNORE_DOUBLE_BLINK = True  # Set False to click on double blink too

# Movement
MOVEMENT_MODE = "RELATIVE"  # Change to "ABSOLUTE" for old behavior
REL_SENSITIVITY = 2.5       # Increase for faster cursor
```
