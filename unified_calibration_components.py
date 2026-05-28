"""Unified calibration module core classes."""

from __future__ import annotations

from math import hypot

import cv2
import numpy as np

from config.settings import _get_bool, _get_float, _get_int, _get_str
from models.robot_state import PIDConstants


class ConfigManager:
    """Registry for runtime configuration values used by the unified module."""

    def __init__(self) -> None:
        self._system_configs = {
            "MAIN_TARGET_HZ": _get_float("MAIN_TARGET_HZ", 30.0),
            "MAIN_CAMERA_INDEX": _get_int("MAIN_CAMERA_INDEX", 0),
            "MAIN_FLIP_FRAME": _get_bool("MAIN_FLIP_FRAME", False),
        }
        self._debug_configs = {
            "MAIN_DEBUG_MODE": _get_bool("MAIN_DEBUG_MODE", False),
            "MAIN_SHOW_PREVIEW": _get_bool("MAIN_SHOW_PREVIEW", False),
            "MAIN_SHOW_GUIDANCE_OVERLAY": _get_bool(
                "MAIN_SHOW_GUIDANCE_OVERLAY",
                True,
            ),
        }
        self._video_configs = {
            "MAIN_WRITE_DEBUG_VIDEO": _get_bool("MAIN_WRITE_DEBUG_VIDEO", False),
            "MAIN_DEBUG_VIDEO_OUTPUT": _get_str(
                "MAIN_DEBUG_VIDEO_OUTPUT",
                "main_debug.mp4",
            ),
            "MAIN_VIDEO_OUTPUT_FPS": _get_float("MAIN_VIDEO_OUTPUT_FPS", 20.0),
        }
        self._stream_configs = {
            "MAIN_HTTPS_STREAM_ENABLED": _get_bool("MAIN_HTTPS_STREAM_ENABLED", False),
            "MAIN_HTTPS_STREAM_HOST": _get_str("MAIN_HTTPS_STREAM_HOST", "127.0.0.1"),
            "MAIN_HTTPS_STREAM_PORT": _get_int("MAIN_HTTPS_STREAM_PORT", 8443),
            "MAIN_HTTPS_STREAM_PUBLIC": _get_bool("MAIN_HTTPS_STREAM_PUBLIC", False),
            "MAIN_HTTPS_STREAM_PATH": _get_str("MAIN_HTTPS_STREAM_PATH", "/stream.mjpg"),
            "MAIN_HTTPS_SNAPSHOT_PATH": _get_str(
                "MAIN_HTTPS_SNAPSHOT_PATH",
                "/snapshot.jpg",
            ),
            "MAIN_HTTPS_STATUS_PATH": _get_str("MAIN_HTTPS_STATUS_PATH", "/status"),
            "MAIN_HTTPS_TOKEN": _get_str("MAIN_HTTPS_TOKEN", ""),
            "MAIN_HTTPS_CERT_FILE": _get_str(
                "MAIN_HTTPS_CERT_FILE",
                "certs/main_stream_cert.pem",
            ),
            "MAIN_HTTPS_KEY_FILE": _get_str(
                "MAIN_HTTPS_KEY_FILE",
                "certs/main_stream_key.pem",
            ),
            "MAIN_HTTPS_SELF_SIGNED_DAYS": _get_int("MAIN_HTTPS_SELF_SIGNED_DAYS", 365),
        }
        self._vp_inner_thresh = _get_float("VP_INNER_THRESH", 3.0)
        self._vp_outer_thresh = _get_float("VP_OUTER_THRESH", 5.0)
        self._danger_margin_px = _get_int("DANGER_MARGIN_PX", 100)
        self._danger_nudge_deg = _get_float("DANGER_NUDGE_DEG", 5.0)

    def get_system_configs(self) -> dict:
        """Return system loop and camera configuration."""
        return dict(self._system_configs)

    def get_debug_configs(self) -> dict:
        """Return debug and visualization toggles."""
        return dict(self._debug_configs)

    def get_video_configs(self) -> dict:
        """Return debug video output settings."""
        return dict(self._video_configs)

    def get_stream_configs(self) -> dict:
        """Return HTTPS stream configuration values."""
        return dict(self._stream_configs)

    def get_vp_thresholds(self) -> tuple[float, float]:
        """Return vanishing-point hysteresis thresholds (inner, outer)."""
        return self._vp_inner_thresh, self._vp_outer_thresh

    def get_danger_margins(self) -> tuple[int, float]:
        """Return danger margin in pixels and fixed nudge angle in degrees."""
        return self._danger_margin_px, self._danger_nudge_deg


class VisionProcessor:
    """Frame pre-processor and Stage-1 line extractor."""

    def __init__(self, roi_height_pct: float) -> None:
        self._roi_height_pct = max(0.0, min(1.0, roi_height_pct))
        self._blur_w = _get_int("VISION_BLUR_KERNEL_W", 5)
        self._blur_h = _get_int("VISION_BLUR_KERNEL_H", 5)
        self._canny_low = _get_int("VISION_CANNY_LOW", 50)
        self._canny_high = _get_int("VISION_CANNY_HIGH", 150)
        self._hough_threshold = _get_int("VISION_HOUGH_THRESHOLD", 40)
        self._hough_min_line_length = _get_int("VISION_HOUGH_MIN_LINE_LENGTH", 40)
        self._hough_max_line_gap = _get_int("VISION_HOUGH_MAX_LINE_GAP", 20)
        self._min_abs_slope = _get_float("VISION_MIN_ABS_SLOPE", 0.3)

    def process_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        """Extract raw Hough line segments from the configured top ROI."""
        if frame is None or frame.size == 0:
            return []

        frame_height = frame.shape[0]
        roi_height = max(1, int(frame_height * self._roi_height_pct))
        roi = frame[:roi_height, :]

        if len(roi.shape) == 3 and roi.shape[2] == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi

        blur_w = self._blur_w if self._blur_w % 2 == 1 else self._blur_w + 1
        blur_h = self._blur_h if self._blur_h % 2 == 1 else self._blur_h + 1
        preprocessed = cv2.GaussianBlur(gray, (blur_w, blur_h), 0)
        edges = cv2.Canny(preprocessed, self._canny_low, self._canny_high)

        raw_lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self._hough_threshold,
            minLineLength=self._hough_min_line_length,
            maxLineGap=self._hough_max_line_gap,
        )
        if raw_lines is None:
            return []

        return [
            (int(x1), int(y1), int(x2), int(y2))
            for [[x1, y1, x2, y2]] in raw_lines.tolist()
        ]

    def _apply_geometric_filter(
        self,
        lines: list[tuple[int, int, int, int]],
    ) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]] | None:
        """Select the strongest negative and positive slope lines."""
        if not lines:
            return None

        best_negative: tuple[int, int, int, int] | None = None
        best_positive: tuple[int, int, int, int] | None = None
        best_negative_len = 0.0
        best_positive_len = 0.0

        for x1, y1, x2, y2 in lines:
            dx = x2 - x1
            if dx == 0:
                continue

            slope = (y2 - y1) / dx
            if abs(slope) < self._min_abs_slope:
                continue

            length = hypot(dx, y2 - y1)
            line = (x1, y1, x2, y2)
            if slope < 0 and length > best_negative_len:
                best_negative = line
                best_negative_len = length
            elif slope > 0 and length > best_positive_len:
                best_positive = line
                best_positive_len = length

        if best_negative is None or best_positive is None:
            return None
        return best_negative, best_positive


class GeometryCalculator:
    """Stateless geometry helpers for line intersection and mapping."""

    @staticmethod
    def calculate_vanishing_point(
        line1: tuple[int, int, int, int],
        line2: tuple[int, int, int, int],
    ) -> tuple[int, int] | None:
        """Return the intersection point of two lines, or None if parallel."""
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2

        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denominator == 0:
            return None

        det1 = x1 * y2 - y1 * x2
        det2 = x3 * y4 - y3 * x4

        px = (det1 * (x3 - x4) - (x1 - x2) * det2) / denominator
        py = (det1 * (y3 - y4) - (y1 - y2) * det2) / denominator
        return int(round(px)), int(round(py))

    @staticmethod
    def calculate_bottom_intercepts(
        line1: tuple[int, int, int, int],
        line2: tuple[int, int, int, int],
        frame_height: int,
    ) -> tuple[int, int]:
        """Return x-intercepts where each line crosses y=frame_height."""
        y_target = float(frame_height)

        def x_at_y(line: tuple[int, int, int, int]) -> int:
            x1, y1, x2, y2 = line
            if y2 == y1:
                return int(x1)
            if x2 == x1:
                return int(x1)
            t = (y_target - y1) / (y2 - y1)
            x = x1 + t * (x2 - x1)
            return int(round(x))

        return x_at_y(line1), x_at_y(line2)

    @staticmethod
    def map_vp_to_angle(vp_x: int, frame_width: int) -> float:
        """Map vanishing-point x-coordinate to linear proxy heading angle."""
        if frame_width <= 0:
            return 90.0
        return (180.0 / float(frame_width)) * float(vp_x)


class SteeringController:
    """State-machine governor implementing vision-lost, danger, and tracking stages."""

    def __init__(
        self,
        pid_constants: PIDConstants,
        danger_margin: int,
        nudge_deg: float,
        inner_thresh: float,
        outer_thresh: float,
    ) -> None:
        self._pid = pid_constants
        self._danger_margin = max(0, int(danger_margin))
        self._nudge_deg = float(nudge_deg)
        self._inner_thresh = abs(float(inner_thresh))
        self._outer_thresh = max(abs(float(outer_thresh)), self._inner_thresh)
        self._tracking_active = False
        self._last_error = 0.0

    def compute_steering(
        self,
        vp_angle: float | None,
        left_intercept: int | None,
        right_intercept: int | None,
        frame_width: int,
    ) -> tuple[float, str]:
        """Return steering angle and active state according to 3-stage logic."""
        # Stage 1: Vision Lost (Gapping)
        if vp_angle is None or left_intercept is None or right_intercept is None:
            self._tracking_active = False
            self._last_error = 0.0
            return 90.0, "GAPPING"

        # Stage 3: Danger Zone override (bypass PD)
        left_margin = self._danger_margin
        right_margin = max(0, int(frame_width) - self._danger_margin)
        if left_intercept > left_margin:
            self._tracking_active = False
            self._last_error = 0.0
            return 90.0 + self._nudge_deg, "DANGER_LEFT"
        if right_intercept < right_margin:
            self._tracking_active = False
            self._last_error = 0.0
            return 90.0 - self._nudge_deg, "DANGER_RIGHT"

        # Stage 2: Tracking with hysteresis
        error = float(vp_angle) - 90.0
        abs_error = abs(error)
        if abs_error <= self._inner_thresh:
            self._tracking_active = False
            self._last_error = 0.0
            return 90.0, "TRACKING_COAST"

        if abs_error > self._outer_thresh:
            self._tracking_active = True

        if not self._tracking_active:
            return 90.0, "TRACKING_COAST"

        pd_correction = self._apply_pd(error)
        steering_angle = max(0.0, min(180.0, 90.0 + pd_correction))
        return steering_angle, "TRACKING_PD"

    def _apply_pd(self, error: float) -> float:
        """Apply proportional-derivative smoothing and return steering correction."""
        derivative = error - self._last_error
        self._last_error = error
        return (self._pid.kp * error) + (self._pid.kd * derivative)
