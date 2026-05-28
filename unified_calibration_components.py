"""Unified calibration module core classes."""

from __future__ import annotations

from math import hypot

import cv2
import numpy as np

from config.settings import _get_bool, _get_float, _get_int, _get_str


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
