# Vision Detector API

Module: `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/vision/detector.py`

## Public API

- `_angle_diff(a: float, b: float) -> float`
  - Returns minimum heading difference in `[0, 90]` with 180-degree wrap handling.

- `class LineDetector`
  - `__init__(self, state: models.robot_state.RobotState) -> None`
  - `get_reference_angle(self, frame: np.ndarray) -> Optional[float]`
  - `get_reference_angle_debug(self, frame: np.ndarray) -> tuple[Optional[float], dict[str, Any]]`

## Debug Contract

`get_reference_angle_debug` returns a dictionary including stage images and telemetry keys such as:

- `gray`, `roi`, `preprocessed`, `edges`, `hough_vis`, `grouped_vis`
- `lines_count`, `groups_count`, `reference_group_index`, `selected_group_bbox`
- `theta_horizontal`, `theta_candidate`, `horizontal_ok`, `sanity_ok`, `theta_output`, `stale_output`
