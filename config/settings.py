"""Environment-backed settings helpers and exported runtime constants."""

from __future__ import annotations

import os


def _get_str(name: str, default: str) -> str:
    """Get string setting from environment."""
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    """Get integer setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """Get float setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    """Get boolean setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


MAIN_TARGET_HZ = _get_float("MAIN_TARGET_HZ", 30.0)
MAIN_CAMERA_INDEX = _get_int("MAIN_CAMERA_INDEX", 0)
MAIN_CSV_LOG_FILE = _get_str("MAIN_CSV_LOG_FILE", "run_log.csv")
MAIN_FLIP_FRAME = _get_bool("MAIN_FLIP_FRAME", False)
MAIN_TERMINAL_LOG = _get_bool("MAIN_TERMINAL_LOG", True)
MAIN_DEBUG_MODE = _get_bool("MAIN_DEBUG_MODE", False)
MAIN_SHOW_PREVIEW = _get_bool("MAIN_SHOW_PREVIEW", False)
MAIN_SHOW_GUIDANCE_OVERLAY = _get_bool("MAIN_SHOW_GUIDANCE_OVERLAY", True)
MAIN_SHOW_DETECTOR_DEBUG = _get_bool("MAIN_SHOW_DETECTOR_DEBUG", False)
MAIN_WRITE_DEBUG_VIDEO = _get_bool("MAIN_WRITE_DEBUG_VIDEO", False)
MAIN_DEBUG_VIDEO_OUTPUT = _get_str("MAIN_DEBUG_VIDEO_OUTPUT", "main_debug.mp4")
MAIN_VIDEO_OUTPUT_FPS = _get_float("MAIN_VIDEO_OUTPUT_FPS", 20.0)
MAIN_DEBUG_FRAME_SCALE = _get_float("MAIN_DEBUG_FRAME_SCALE", 1.25)
MAIN_DEBUG_OVERLAY_SCALE = _get_float("MAIN_DEBUG_OVERLAY_SCALE", 0.75)
MAIN_CAMERA_RETRY_LIMIT = _get_int("MAIN_CAMERA_RETRY_LIMIT", 3)
MAIN_VIDEO_RETRY_LIMIT = _get_int("MAIN_VIDEO_RETRY_LIMIT", 5)
MAIN_HARDWARE_RETRY_LIMIT = _get_int("MAIN_HARDWARE_RETRY_LIMIT", 5)
MAIN_HTTPS_STREAM_ENABLED = _get_bool("MAIN_HTTPS_STREAM_ENABLED", False)
MAIN_HTTPS_STREAM_HOST = _get_str("MAIN_HTTPS_STREAM_HOST", "127.0.0.1")
MAIN_HTTPS_STREAM_PORT = _get_int("MAIN_HTTPS_STREAM_PORT", 8443)
MAIN_HTTPS_STREAM_PUBLIC = _get_bool("MAIN_HTTPS_STREAM_PUBLIC", False)
MAIN_HTTPS_STREAM_PATH = _get_str("MAIN_HTTPS_STREAM_PATH", "/stream.mjpg")
MAIN_HTTPS_SNAPSHOT_PATH = _get_str("MAIN_HTTPS_SNAPSHOT_PATH", "/snapshot.jpg")
MAIN_HTTPS_STATUS_PATH = _get_str("MAIN_HTTPS_STATUS_PATH", "/status")
MAIN_HTTPS_TOKEN = _get_str("MAIN_HTTPS_TOKEN", "")
MAIN_HTTPS_CERT_FILE = _get_str("MAIN_HTTPS_CERT_FILE", "certs/main_stream_cert.pem")
MAIN_HTTPS_KEY_FILE = _get_str("MAIN_HTTPS_KEY_FILE", "certs/main_stream_key.pem")
MAIN_HTTPS_SELF_SIGNED_DAYS = _get_int("MAIN_HTTPS_SELF_SIGNED_DAYS", 365)

PROCESS_VIDEO_CSV_OUTPUT = _get_str("PROCESS_VIDEO_CSV_OUTPUT", "video_log.csv")
PROCESS_VIDEO_OUTPUT = _get_str("PROCESS_VIDEO_OUTPUT", "processed_video.mp4")
PROCESS_VIDEO_SEND_TO_SERVO = _get_bool("PROCESS_VIDEO_SEND_TO_SERVO", True)
PROCESS_VIDEO_TERMINAL_LOG = _get_bool("PROCESS_VIDEO_TERMINAL_LOG", False)
PROCESS_VIDEO_SHOW_GUIDANCE_OVERLAY = _get_bool("PROCESS_VIDEO_SHOW_GUIDANCE_OVERLAY", False)
PROCESS_VIDEO_SHOW_DETECTOR_DEBUG = _get_bool("PROCESS_VIDEO_SHOW_DETECTOR_DEBUG", False)
PROCESS_VIDEO_START_CALIB_THRESHOLD_DEG = _get_float("PROCESS_VIDEO_START_CALIB_THRESHOLD_DEG", 5.0)
PROCESS_VIDEO_STOP_CALIB_THRESHOLD_DEG = _get_float("PROCESS_VIDEO_STOP_CALIB_THRESHOLD_DEG", 3.0)
PROCESS_VIDEO_FLIP_FRAME = _get_bool("PROCESS_VIDEO_FLIP_FRAME", False)
PROCESS_VIDEO_FRAME_SLEEP_MS = _get_float("PROCESS_VIDEO_FRAME_SLEEP_MS", 0.0)

PID_KP = _get_float("PID_KP", 1.0)
PID_KI = _get_float("PID_KI", 0.05)
PID_KD = _get_float("PID_KD", 0.1)
PID_CALIBRATION_CLEAR_TOLERANCE_DEG = _get_float("PID_CALIBRATION_CLEAR_TOLERANCE_DEG", 1.0)
SERVO_CENTER_ANGLE = _get_float("SERVO_CENTER_ANGLE", 90.0)
MAX_STEERING_OFFSET = _get_float("MAX_STEERING_OFFSET", 30.0)
ROI_HEIGHT_PCT = _get_float("ROI_HEIGHT_PCT", 0.6)
ROI_TOP_WIDTH_PCT = _get_float("ROI_TOP_WIDTH_PCT", 0.75)
ROI_BOTTOM_WIDTH_PCT = _get_float("ROI_BOTTOM_WIDTH_PCT", 1.0)
ROBOT_DEBUG_MODE = _get_bool("ROBOT_DEBUG_MODE", False)

VISION_CLAHE_CLIP_LIMIT = _get_float("VISION_CLAHE_CLIP_LIMIT", 2.0)
VISION_CLAHE_TILE_GRID_W = _get_int("VISION_CLAHE_TILE_GRID_W", 8)
VISION_CLAHE_TILE_GRID_H = _get_int("VISION_CLAHE_TILE_GRID_H", 8)
VISION_BLUR_KERNEL_W = _get_int("VISION_BLUR_KERNEL_W", 5)
VISION_BLUR_KERNEL_H = _get_int("VISION_BLUR_KERNEL_H", 5)
VISION_CANNY_LOW = _get_int("VISION_CANNY_LOW", 50)
VISION_CANNY_HIGH = _get_int("VISION_CANNY_HIGH", 150)
VISION_HOUGH_THRESHOLD = _get_int("VISION_HOUGH_THRESHOLD", 40)
VISION_HOUGH_MIN_LINE_LENGTH = _get_int("VISION_HOUGH_MIN_LINE_LENGTH", 40)
VISION_HOUGH_MAX_LINE_GAP = _get_int("VISION_HOUGH_MAX_LINE_GAP", 20)
VISION_MIN_ABS_SLOPE = _get_float("VISION_MIN_ABS_SLOPE", 0.3)
VISION_CLUSTER_ANGLE_DEG = _get_float("VISION_CLUSTER_ANGLE_DEG", 7.5)
VISION_CLUSTER_DIST_PX = _get_float("VISION_CLUSTER_DIST_PX", 30.0)
VISION_MIN_GROUP_TOTAL_LENGTH_PX = _get_float("VISION_MIN_GROUP_TOTAL_LENGTH_PX", 100.0)

VP_INNER_THRESH = _get_float("VP_INNER_THRESH", 3.0)
VP_OUTER_THRESH = _get_float("VP_OUTER_THRESH", 5.0)
DANGER_MARGIN_PX = _get_int("DANGER_MARGIN_PX", 100)
DANGER_NUDGE_DEG = _get_float("DANGER_NUDGE_DEG", 5.0)
MAIN_FRAME_WIDTH = _get_int("MAIN_FRAME_WIDTH", 640)
MAIN_FRAME_HEIGHT = _get_int("MAIN_FRAME_HEIGHT", 480)


__all__ = [name for name in globals() if name.isupper() or name.startswith("_get_")]
