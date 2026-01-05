import unittest

from src.config import Config
from src.presets import PRESETS, apply_preset, next_preset_name


class DummyConfig:
    HEAD_SPEED_MIN = -1.0
    HEAD_EXP = -1.0
    HEAD_MICRO_GAIN = -1.0
    HEAD_MICRO_RADIUS = -1.0
    HEAD_PRECISION_RADIUS = -1.0
    SMOOTHING_MIN_CUTOFF = -1.0
    SMOOTHING_BETA = -1.0
    MOUSE_SPEED_COEFF = -1.0


class PresetTests(unittest.TestCase):
    def test_preset_override_keys_exist_in_config(self):
        for preset in PRESETS.values():
            for key in preset.overrides.keys():
                self.assertTrue(
                    hasattr(Config, key),
                    msg=f"Preset {preset.name} references unknown Config key: {key}",
                )

    def test_apply_preset_sets_expected_values(self):
        applied = apply_preset(DummyConfig, "legacy")
        self.assertEqual(applied, "legacy")
        self.assertEqual(DummyConfig.ACTIVE_PRESET, "legacy")
        self.assertEqual(DummyConfig.HEAD_SPEED_MIN, 140.0)
        self.assertEqual(DummyConfig.HEAD_EXP, 0.7)
        self.assertEqual(DummyConfig.HEAD_MICRO_GAIN, 1.0)
        self.assertEqual(DummyConfig.HEAD_MICRO_RADIUS, 3.0)
        self.assertEqual(DummyConfig.HEAD_PRECISION_RADIUS, 8.0)
        self.assertEqual(DummyConfig.SMOOTHING_MIN_CUTOFF, 0.6)
        self.assertEqual(DummyConfig.SMOOTHING_BETA, 0.003)
        self.assertEqual(DummyConfig.MOUSE_SPEED_COEFF, 15.0)

    def test_unknown_preset_falls_back_to_default(self):
        applied = apply_preset(DummyConfig, "does-not-exist")
        self.assertEqual(applied, "precision")
        self.assertEqual(DummyConfig.ACTIVE_PRESET, "precision")

    def test_next_preset_name_cycles(self):
        self.assertEqual(next_preset_name(None), "precision")
        self.assertEqual(next_preset_name("precision"), "balanced")


if __name__ == "__main__":
    unittest.main()

