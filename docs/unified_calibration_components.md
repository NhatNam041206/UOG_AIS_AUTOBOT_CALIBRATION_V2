# Unified Calibration Components

This module contains the first four core classes for the Unified Calibration architecture:

- `ConfigManager`: Centralizes environment-backed runtime settings using the legacy `config.settings` helpers exactly as specified.
- `VisionProcessor`: Implements Stage 1 frame processing (top ROI extraction, grayscale/blur/Canny/Hough) and provides `_apply_geometric_filter` to select opposing-slope lane candidates.
- `GeometryCalculator`: Stateless math utilities for vanishing-point intersection, bottom intercepts, and VP-angle mapping.
- `SteeringController`: Core 3-stage state machine for vision loss fallback, danger-zone overrides, and hysteresis-driven PD tracking.

## File Location

- Module: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/unified_calibration_components.py`

## Public Classes and Methods

### `ConfigManager`

- `__init__(self) -> None`
- `get_system_configs(self) -> dict`
- `get_debug_configs(self) -> dict`
- `get_video_configs(self) -> dict`
- `get_stream_configs(self) -> dict`
- `get_vp_thresholds(self) -> tuple[float, float]`
- `get_danger_margins(self) -> tuple[int, float]`

### `VisionProcessor`

- `__init__(self, roi_height_pct: float) -> None`
- `process_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]`
- `_apply_geometric_filter(self, lines: list[tuple[int, int, int, int]]) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]] | None`

### `GeometryCalculator`

- `calculate_vanishing_point(line1: tuple[int, int, int, int], line2: tuple[int, int, int, int]) -> tuple[int, int] | None`
- `calculate_bottom_intercepts(line1: tuple[int, int, int, int], line2: tuple[int, int, int, int], frame_height: int) -> tuple[int, int]`
- `map_vp_to_angle(vp_x: int, frame_width: int) -> float`

### `SteeringController`

- `__init__(self, pid_constants: PIDConstants, danger_margin: int, nudge_deg: float, inner_thresh: float, outer_thresh: float) -> None`
- `compute_steering(self, vp_angle: float | None, left_intercept: int | None, right_intercept: int | None, frame_width: int) -> tuple[float, str]`
- `_apply_pd(self, error: float) -> float`

## Notes

- The module currently implements configuration, Stage 1 vision extraction, stateless geometry math, and steering state-machine logic.
- Telemetry and facade orchestration classes are intentionally left for subsequent implementation phases.
