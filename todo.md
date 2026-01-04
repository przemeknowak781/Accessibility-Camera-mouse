# Project: GestureMouse (Lightweight Hand-Tracking Mouse Controller)

## 1. Project Setup & Environment
- [x] Initialize Python environment (3.10+ recommended).
- [x] Install dependencies:
    - `opencv-python` (Frame capture & processing)
    - `mediapipe` (Hand tracking backend)
    - `numpy` (Math operations)
    - `autopy` OR `pynput` (Mouse control - prioritize autopy for latency)
    - `screeninfo` (Monitor resolution detection)

## 2. Core Vision Pipeline (MediaPipe)
- [x] Create `HandDetector` class encapsulating `mediapipe.solutions.hands`.
- [x] Configure MediaPipe parameters for performance:
    - `static_image_mode=False`
    - `max_num_hands=1`
    - `min_detection_confidence=0.7`
    - `min_tracking_confidence=0.5`
- [x] Implement `findHands` method to process RGB frames.
- [x] Implement `findPosition` method to return landmark coordinates (specifically Index Tip ID:8 and Thumb Tip ID:4).

## 3. Signal Processing & Coordinate Mapping
- [x] Implement **Frame Reduction/Mapping**:
    - Map camera coordinates (e.g., 640x480) to screen resolution (e.g., 1920x1080).
    - Add a "Frame Margin" to allow reaching screen edges without moving hand out of camera view.
    - Formula: `x_screen = interp(x_cam, (frame_margin, cam_w - frame_margin), (0, screen_w))`
- [x] Implement **One Euro Filter** class (or equivalent adaptive smoothing algorithm) based on Casiez et al. (2012).
    - *Goal:* Eliminate cursor jitter while maintaining responsiveness.
    - Parameters to tune: `min_cutoff` (jitter reduction), `beta` (lag reduction).

## 4. Interaction Logic (Controller)
- [x] **Movement Logic:**
    - Use Index Finger Tip (ID:8) as the cursor pointer.
    - Apply smoothed coordinates to set mouse position.
- [x] **Click Logic:**
    - Calculate Euclidean distance between Index Tip (ID:8) and Thumb Tip (ID:4).
    - Define a threshold distance for activation (e.g., < 30px).
    - Implement a "Click State" debouncing mechanism to prevent accidental double clicks (wait for fingers to separate before next click).

## 5. Optimization & Threading
- [x] Calculate FPS and display on screen for performance monitoring.
- [x] Ensure the main loop runs efficiently (avoid blocking calls).
- [ ] (Optional) Move frame capturing to a separate thread if latency issues arise.

## 6. Testing & Refinement
- [ ] Test cursor reachability (corners of the screen).
- [ ] Tune One Euro Filter parameters (`min_cutoff`, `beta`) for optimal "feel".
- [ ] Verify CPU usage stays low (<10-15% on modern CPU).
