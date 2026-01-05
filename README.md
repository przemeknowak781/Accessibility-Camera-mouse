# Accessibility Camera Mouse

Handsteer is a lightweight, camera‑based mouse controller designed for accessibility use‑cases. It uses hand tracking plus optional head and eye tracking to control the cursor without a physical mouse.

## Features
- Hand cursor with smoothing and acceleration.
- Relative hand mode for touchpad-style movement.
- Pinch‑to‑hold for drag & drop.
- Blink click (optional).
- Head mode for hands‑free control.
- Eye‑hand hybrid: eyes for fast positioning, hand for fine tuning.
- On‑screen HUD with live tuning.
- Calibration flow for eye tracking (4 corners).

## Requirements
- Windows 10/11
- Python 3.10+
- Camera (webcam)
- Optional: `autopy` (legacy, may fail to install on newer Python versions)

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

Or double‑click:
```
run.bat
```

## Controls (Runtime)
General:
- `Space` toggle pause
- `Esc` quit
- `V` toggle preview on/off (headless mode)

Modes:
- `0` RELATIVE (touchpad-style hand movement)
- `1` ABSOLUTE (hand cursor)
- `2` HEAD (head‑only)
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

Hand fine (eye‑hand mode):
- Fine scale: `l` / `;`

## Eye Calibration
In `EYE_HYBRID` or `EYE_HAND` mode:
1) Look at **Bottom Left** → press `Enter` and hold still for ~1s
2) Look at **Bottom Right** → press `Enter` and hold still for ~1s
3) Look at **Top Right** → press `Enter` and hold still for ~1s
4) Look at **Top Left** → press `Enter` and hold still for ~1s

The gaze dot shows your current mapped eye position. Recalibrate anytime with `c`.

## Configuration
Edit `src/config.py` for defaults:
- Movement mode, thresholds, smoothing, and acceleration.
- Head tracking sensitivity and speed.
- Eye tracking gain and smoothing.

## Troubleshooting
- If performance drops when minimized, press `V` to disable preview.
- If mouse movement feels off on multi‑monitor setups, set `MONITOR_INDEX` in `src/config.py`.
- If autopy drag fails, switch to `MOUSE_BACKEND = "pynput"`.

## Safety
This app controls the system mouse. Keep `Esc` available for quick exit.
