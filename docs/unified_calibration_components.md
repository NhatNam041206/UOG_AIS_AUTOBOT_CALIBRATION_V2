# Unified Calibration Components

This module now provides the full unified runtime facade and integrates the utility APIs specified in `utilities_spec.md`.

## File Location

- Module: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/unified_calibration_components.py`

## Implemented Classes

- `ConfigManager`
  - Loads runtime `.env` values via `config.settings` helper accessors.
  - Exposes grouped getters: system/debug/video/stream configs + VP/danger thresholds.

- `VisionProcessor`
  - Top-ROI extraction and Canny/Hough line extraction.
  - Geometric line pair selection with opposite slope filter.

- `GeometryCalculator`
  - Vanishing point intersection, bottom intercept projection, and VP-to-angle mapping.

- `SteeringController`
  - 3-stage steering state machine:
    - `GAPPING`
    - `DANGER_LEFT` / `DANGER_RIGHT`
    - `TRACKING_COAST` / `TRACKING_PD`

- `TelemetryLogger`
  - Bridges to `runtime.video_runtime_helpers` APIs for CSV, overlays, debug panel, video writer, and loop sleep.
  - Bridges to `runtime.https_stream` for shared-frame publishing and HTTPS MJPEG serving.
  - Writes a superset main CSV schema aligned to `utilities_spec.md`.

- `UnifiedCalibrator`
  - Main orchestrator for frame capture, processing, steering decision, visualization, telemetry, and loop timing.
  - Integrates `vision.detector.LineDetector` debug output.
  - Supports debug visualizer mode selection via `MAIN_DEBUG_VISUALIZER` (`imshow`, `video`, or `both`) when `MAIN_DEBUG_MODE=true`.

## Related Utility Modules

- Runtime helpers: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/runtime/video_runtime_helpers.py`
- HTTPS stream: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/runtime/https_stream.py`
- Detector API: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/vision/detector.py`
- Robot state contracts: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/models/robot_state.py`

## Notes

- Runtime configuration should be read through `config.settings` helpers and exported constants.
- The utility modules are intentionally reusable and can be imported independently by future entrypoints.
