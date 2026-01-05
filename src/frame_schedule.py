def schedule_detectors(mode, frame_id, blink_enabled, long_blink_enabled):
    face_needed = blink_enabled or long_blink_enabled or mode in (
        "HEAD",
        "EYE_HYBRID",
        "EYE_HAND",
    )
    hand_needed = mode in ("ABSOLUTE", "RELATIVE", "TILT_HYBRID", "EYE_HAND")
    even = (frame_id % 2) == 0

    if mode == "HEAD":
        return False, face_needed
    if mode == "EYE_HYBRID":
        return False, face_needed and even
    if mode == "EYE_HAND":
        return hand_needed and not even, face_needed and even
    if mode == "TILT_HYBRID":
        if face_needed:
            return not even, even
        return True, False
    return hand_needed, face_needed

