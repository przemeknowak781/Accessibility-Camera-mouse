from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    overrides: Mapping[str, Any]


DEFAULT_PRESET_NAME = "precision"


PRESETS: dict[str, Preset] = {
    # Default: optimized for small-target clicking (slow moves) without losing top speed.
    "precision": Preset(
        name="precision",
        description="More micro-precision; less inertia near slow moves.",
        overrides={
            "HEAD_SPEED_MIN": 0.0,
            "HEAD_EXP": 1.6,
            "HEAD_MICRO_GAIN": 0.7,
            "HEAD_MICRO_RADIUS": 6.0,
            "HEAD_PRECISION_RADIUS": 16.0,
            "MOUSE_SPEED_COEFF": 35.0,
        },
    ),
    "balanced": Preset(
        name="balanced",
        description="A middle ground between precision and speed.",
        overrides={
            "HEAD_SPEED_MIN": 20.0,
            "HEAD_EXP": 1.25,
            "HEAD_MICRO_GAIN": 0.85,
            "HEAD_MICRO_RADIUS": 5.0,
            "HEAD_PRECISION_RADIUS": 14.0,
            "MOUSE_SPEED_COEFF": 30.0,
        },
    ),
    "fast": Preset(
        name="fast",
        description="Quicker mid-range movement; harder micro-stops.",
        overrides={
            "HEAD_SPEED_MIN": 80.0,
            "HEAD_EXP": 0.95,
            "HEAD_MICRO_GAIN": 1.0,
            "HEAD_MICRO_RADIUS": 4.0,
            "HEAD_PRECISION_RADIUS": 10.0,
            "MOUSE_SPEED_COEFF": 45.0,
        },
    ),
    "turbo": Preset(
        name="turbo",
        description="Maximum speed, minimal damping - for large screens.",
        overrides={
            "HEAD_SPEED_MIN": 120.0,
            "HEAD_SPEED_MAX": 3200.0,
            "HEAD_EXP": 0.8,
            "HEAD_MICRO_GAIN": 1.2,
            "HEAD_MICRO_RADIUS": 3.0,
            "HEAD_PRECISION_RADIUS": 8.0,
            "HEAD_SENSITIVITY": 8.0,
            "MOUSE_SPEED_COEFF": 55.0,
            "SNAP_STRENGTH": 0.6,
        },
    ),
    "swift": Preset(
        name="swift",
        description="Fast but smooth - good for general use.",
        overrides={
            "HEAD_SPEED_MIN": 60.0,
            "HEAD_EXP": 1.0,
            "HEAD_MICRO_GAIN": 0.9,
            "HEAD_MICRO_RADIUS": 5.0,
            "HEAD_PRECISION_RADIUS": 12.0,
            "HEAD_NEUTRAL_ALPHA": 0.06,
            "MOUSE_SPEED_COEFF": 40.0,
            "SMOOTHING_MIN_CUTOFF": 0.7,
        },
    ),
    "snappy": Preset(
        name="snappy",
        description="Quick response with strong snap assist.",
        overrides={
            "HEAD_SPEED_MIN": 100.0,
            "HEAD_EXP": 0.85,
            "HEAD_MICRO_GAIN": 1.1,
            "HEAD_MICRO_RADIUS": 4.0,
            "HEAD_PRECISION_RADIUS": 10.0,
            "MOUSE_SPEED_COEFF": 50.0,
            "SNAP_STRENGTH": 0.65,
            "SNAP_RADIUS": 100.0,
            "SNAP_LOCK_RADIUS": 15.0,
        },
    ),
    "stable": Preset(
        name="stable",
        description="Extra stability for noisy tracking (slightly more lag).",
        overrides={
            "HEAD_SPEED_MIN": 0.0,
            "HEAD_EXP": 1.45,
            "HEAD_MICRO_GAIN": 0.75,
            "HEAD_MICRO_RADIUS": 6.0,
            "HEAD_PRECISION_RADIUS": 18.0,
            "SMOOTHING_MIN_CUTOFF": 0.5,
            "SMOOTHING_BETA": 0.0025,
            "MOUSE_SPEED_COEFF": 28.0,
        },
    ),
    # Previous defaults (kept for quick A/B).
    "legacy": Preset(
        name="legacy",
        description="Previous default tuning (before presets).",
        overrides={
            "HEAD_SPEED_MIN": 140.0,
            "HEAD_EXP": 0.7,
            "HEAD_MICRO_GAIN": 1.0,
            "HEAD_MICRO_RADIUS": 3.0,
            "HEAD_PRECISION_RADIUS": 8.0,
            "SMOOTHING_MIN_CUTOFF": 0.6,
            "SMOOTHING_BETA": 0.003,
            "MOUSE_SPEED_COEFF": 15.0,
        },
    ),
}

PRESET_ORDER = ["precision", "balanced", "fast", "turbo", "swift", "snappy", "stable", "legacy"]


def apply_preset(config, preset_name: str | None) -> str:
    resolved = str(preset_name).strip() if preset_name is not None else ""
    if resolved not in PRESETS:
        resolved = DEFAULT_PRESET_NAME
    preset = PRESETS[resolved]

    for key, value in preset.overrides.items():
        setattr(config, key, value)

    setattr(config, "ACTIVE_PRESET", preset.name)
    return preset.name


def next_preset_name(current: str | None, direction: int = 1) -> str:
    if not PRESET_ORDER:
        return DEFAULT_PRESET_NAME
    if current not in PRESET_ORDER:
        return PRESET_ORDER[0]
    idx = PRESET_ORDER.index(current)
    idx = (idx + (1 if direction >= 0 else -1)) % len(PRESET_ORDER)
    return PRESET_ORDER[idx]

