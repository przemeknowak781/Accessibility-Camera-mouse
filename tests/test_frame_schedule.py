import unittest

from src.frame_schedule import schedule_detectors


class FrameScheduleTests(unittest.TestCase):
    def test_head_runs_face_only(self):
        run_hand, run_face = schedule_detectors("HEAD", 0, False, False)
        self.assertFalse(run_hand)
        self.assertTrue(run_face)

    def test_eye_hand_alternates(self):
        run_hand, run_face = schedule_detectors("EYE_HAND", 0, True, False)
        self.assertFalse(run_hand)
        self.assertTrue(run_face)

        run_hand, run_face = schedule_detectors("EYE_HAND", 1, True, False)
        self.assertTrue(run_hand)
        self.assertFalse(run_face)

    def test_eye_hybrid_alternates_face(self):
        run_hand, run_face = schedule_detectors("EYE_HYBRID", 0, False, False)
        self.assertFalse(run_hand)
        self.assertTrue(run_face)

        run_hand, run_face = schedule_detectors("EYE_HYBRID", 1, False, False)
        self.assertFalse(run_hand)
        self.assertFalse(run_face)

    def test_tilt_hybrid_alternates_when_face_needed(self):
        run_hand, run_face = schedule_detectors("TILT_HYBRID", 0, True, False)
        self.assertFalse(run_hand)
        self.assertTrue(run_face)

        run_hand, run_face = schedule_detectors("TILT_HYBRID", 1, True, False)
        self.assertTrue(run_hand)
        self.assertFalse(run_face)

    def test_tilt_hybrid_runs_hand_only_without_face(self):
        run_hand, run_face = schedule_detectors("TILT_HYBRID", 0, False, False)
        self.assertTrue(run_hand)
        self.assertFalse(run_face)

    def test_absolute_runs_hand_and_optional_face(self):
        run_hand, run_face = schedule_detectors("ABSOLUTE", 0, True, False)
        self.assertTrue(run_hand)
        self.assertTrue(run_face)


if __name__ == "__main__":
    unittest.main()

