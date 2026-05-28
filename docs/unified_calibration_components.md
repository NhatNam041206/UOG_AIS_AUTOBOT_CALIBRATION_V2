# Unified Calibration Components

This module contains the first two core classes for the Unified Calibration architecture:

- `ConfigManager`: Centralizes environment-backed runtime settings using the legacy `config.settings` helpers exactly as specified.
- `VisionProcessor`: Implements Stage 1 frame processing (top ROI extraction, grayscale/blur/Canny/Hough) and provides `_apply_geometric_filter` to select opposing-slope lane candidates.

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

## Notes

- The module intentionally keeps scope limited to configuration and Stage 1 vision extraction.
- Additional architecture classes (geometry, steering, telemetry, facade) are not included in this file yet.
