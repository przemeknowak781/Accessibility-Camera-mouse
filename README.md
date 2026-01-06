# Handsteer

Handsteer is a lightweight, camera-based mouse controller for accessibility. It uses hand tracking and optional head and eye tracking to move the cursor without a physical mouse. The app focuses on precision, stability, and fast switching between control styles.

## Features
- Hand cursor with smoothing and optional acceleration.
- Relative hand mode (touchpad style).
- Pinch-to-hold drag and blink click.
- Head-only mode and eye+head / eye+hand hybrids.
- Smart snapping (UIA-based magnet to clickable targets).
- Snap target marker overlay (always-on-top crosshair).
- Presets for different precision/speed profiles.
- On-screen HUD with live tuning.
- Mini always-on-top preview for throttling-safe mode.

## Requirements
- Windows 10/11
- Python 3.10+
- Webcam
- Optional: `uiautomation` for smart snapping

## Install
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```powershell
python main.py
```

Or double-click:
```
run.bat
```

## Controls (Runtime)
General:
- `Space` toggle pause
- `Esc` quit
- `V` toggle preview on/off
- `M` toggle mini always-on-top window
- `S` toggle smart snapping
- `F6` cycle preset
- Long blink (hold both eyes closed ~0.7s): center cursor

Modes:
- `0` RELATIVE (touchpad-style hand)
- `1` ABSOLUTE (hand cursor)
- `2` HEAD (head-only)
- `3` EYE_HYBRID (eyes + head fine)
- `4` EYE_HAND (eyes + hand fine)
- `5` TILT_HYBRID (hand tilt + fine hand)

Tuning (shown in HUD):
- Accel on/off: `A`
- Accel gain: `[` / `]`

Head:
- Sensitivity: `-` / `=`
- Deadzone: `z` / `x`
- Speed max: `,` / `.`
- Curve exp: `/` / `\`
- Neutral adapt: `n` / `m`
- Micro gain: `u` / `i`
- Stop threshold: `j` / `k`
- Stop hold: `o` / `p`

Eye:
- Gain: `v` / `b`
- Smoothing: `f` / `g`
- Neutral adapt: `q` / `w`
- Calibration: `c` (then press `Enter` at each prompt)

Hand fine (eye-hand mode):
- Fine scale: `l` / `;`

## Presets
Press `F6` to cycle presets:
- `precision` (default): maximum micro-control.
- `balanced`: smooth compromise.
- `fast`: quicker mid-range movement.
- `stable`: extra smoothing for noisy tracking.
- `legacy`: previous defaults for A/B testing.

## Smart Snapping
Smart snapping uses UI Automation (via `uiautomation`) to pull the cursor toward interactive controls.
- Enable/disable with `S`.
- Trigger mode defaults to always-on (see `Config.SNAP_TRIGGER_MODE`).
- Brows raise can be used as a trigger.
- If snapping feels weak, adjust `SNAP_RADIUS` and `SNAP_STRENGTH` in `src/config.py`.

Diagnostics:
- Press `D` to log the element under the cursor (`SNAP_DEBUG` in `events.log`).
- Run `python diagnose_snap.py` to verify UIA availability.
- `snap_debug.txt` records snapper scan traces for deeper troubleshooting.
- Run `python debug_brows.py` to measure brow ratios.

## Configuration
Defaults live in `src/config.py`:
- Camera size and backend (`CAM_BACKEND`: `auto`, `msmf`, `dshow`)
- Movement mode, smoothing, and acceleration
- Head and eye parameters
- Snap tuning (radius, strength, hold, and trigger)
- Monitor selection and mouse backend

## Architecture
Key modules:
- `src/smart_snap.py`: UIA scanning and target selection.
- `src/snap_controller.py`: activation logic, smoothing, and hold.
- `src/mouse_driver.py`: cursor output, snap gravity, and override.
- `src/head_motion.py`: head-based motion and neutral handling.
- `src/face_blink.py`: blink/long-blink/brows detection.
- `src/eye_tracker.py`: gaze mapping and calibration.
- `src/frame_schedule.py`: per-frame detector scheduling.
- `src/window_utils.py`: mini window placement and topmost handling.

## Troubleshooting
- If the preview causes CPU throttling, press `V` or use mini mode (`M`).
- If the camera is blank, try `CAM_BACKEND = "dshow"` in `src/config.py`.
- If snap never finds targets in Chromium-based apps, ensure accessibility is enabled.
- For multi-monitor setups, set `MONITOR_INDEX` in `src/config.py`.

## Tests
```powershell
python -m unittest discover -s tests
```

## Safety
This app controls the system cursor. Keep `Esc` available to quit quickly.
