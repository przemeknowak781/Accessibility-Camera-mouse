def is_camera_stalled(frame_time, now, stall_seconds):
    if frame_time is None or stall_seconds <= 0:
        return False
    return (now - frame_time) >= stall_seconds

