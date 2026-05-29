"""Runtime helpers for CSV, video, camera, overlays, and loop timing."""

from __future__ import annotations

import argparse
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

import cv2
import numpy as np


def init_csv_logger(
    path: str,
    fieldnames: list[str],
    use_daily_layout: bool = True,
) -> tuple[csv.DictWriter, TextIO]:
    """Open CSV append logger with optional legacy daily/timestamp layout."""
    source = Path(path)
    if use_daily_layout:
        now = datetime.now()
        day_folder = f"{now.day}_{now.month}_{now.year}"
        timestamp = f"{now.hour}_{now.minute}"
        stem = source.stem or "run_logs"
        suffix = source.suffix or ".csv"
        base_dir = source.parent if str(source.parent) != "." else Path("logs")
        csv_path = base_dir / day_folder / f"{timestamp}_{stem}{suffix}"
    else:
        suffix = source.suffix or ".csv"
        file_name = source.name if source.name else f"run_logs{suffix}"
        base_dir = source.parent if str(source.parent) != "." else Path("logs")
        csv_path = base_dir / file_name

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    existed = csv_path.exists() and csv_path.stat().st_size > 0
    fileobj = csv_path.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fileobj, fieldnames=fieldnames)
    if not existed:
        writer.writeheader()
        fileobj.flush()
    return writer, fileobj


def print_progress(frame_num: int, total_frames: int) -> None:
    """Print an in-place progress bar."""
    total = max(total_frames, 1)
    progress = min(max(frame_num / total, 0.0), 1.0)
    bar_len = 24
    filled = int(progress * bar_len)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(f"\r[{bar}] {frame_num}/{total_frames}", end="", flush=True)


def init_video(path: str, logger: logging.Logger) -> tuple[cv2.VideoCapture, float, int, int, int]:
    """Open and validate a video capture from file path."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    logger.info("Video initialized: %s (%sx%s @ %.2f fps)", path, width, height, fps)
    return cap, fps, frame_count, width, height


def init_video_writer(path: str, fps: float, width: int, height: int) -> cv2.VideoWriter:
    """Create MP4 video writer."""
    out_path = Path(path)
    if out_path.parent and str(out_path.parent) != ".":
        out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(out_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (int(width), int(height)),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Unable to open video writer at: {path}")
    return writer


def init_live_video_writer(path: str, fps: float, width: int, height: int) -> tuple[cv2.VideoWriter, str]:
    """Create timestamped MP4 writer and return writer + resolved path."""
    src = Path(path)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stem = src.stem or "debug"
    suffix = src.suffix or ".mp4"
    resolved = str(src.with_name(f"{stem}_{ts}{suffix}"))
    return init_video_writer(resolved, fps, width, height), resolved


def configure_terminal_logging(enabled: bool) -> None:
    """Adjust stream handler verbosity for root logger."""
    root = logging.getLogger()
    level = logging.INFO if enabled else logging.ERROR
    root.setLevel(level)
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)


def init_camera(index: int) -> cv2.VideoCapture:
    """Open and validate a camera device."""
    capture = cv2.VideoCapture(int(index))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open camera index {index}")
    return capture


def init_camera_with_retries(index: int, retries: int, logger: logging.Logger) -> cv2.VideoCapture:
    """Try opening camera with bounded retries."""
    attempts = max(1, int(retries))
    for attempt in range(1, attempts + 1):
        try:
            return init_camera(index)
        except RuntimeError:
            logger.warning("Camera init failed (%s/%s)", attempt, attempts)
            if attempt < attempts:
                time.sleep(0.25)
    raise RuntimeError(f"Unable to open camera index {index} after {attempts} retries")


def sleep_remainder(loop_start: float, loop_period: float, logger: logging.Logger) -> None:
    """Sleep to maintain loop period and log overruns."""
    elapsed = time.perf_counter() - float(loop_start)
    remaining = float(loop_period) - elapsed
    if remaining > 0:
        time.sleep(remaining)
    else:
        logger.debug("Loop overrun by %.2f ms", abs(remaining) * 1000.0)


def build_process_video_arg_parser(
    default_input: str = "",
    default_output: str = "processed_video.mp4",
    default_csv: str = "video_log.csv",
    default_send_to_servo: bool = True,
) -> argparse.ArgumentParser:
    """Build parser used by process-video entrypoint."""
    parser = argparse.ArgumentParser(description="Process calibration video")
    parser.add_argument("--input", default=default_input, help="Input video path")
    parser.add_argument("--output", default=default_output, help="Output video path")
    parser.add_argument("--csv-output", default=default_csv, help="CSV output path")
    parser.add_argument("--send-to-servo", action="store_true", default=default_send_to_servo)
    parser.add_argument("--no-send-to-servo", action="store_false", dest="send_to_servo")
    return parser


def build_main_arg_parser(
    default_camera_index: int = 0,
    default_target_hz: float = 30.0,
    default_csv_log_file: str = "run_logs.csv",
) -> argparse.ArgumentParser:
    """Build parser used by main realtime entrypoint."""
    parser = argparse.ArgumentParser(description="Unified realtime calibration")
    parser.add_argument("--camera-index", type=int, default=default_camera_index)
    parser.add_argument("--target-hz", type=float, default=default_target_hz)
    parser.add_argument("--csv-log-file", default=default_csv_log_file)
    parser.add_argument("--flip-frame", action="store_true")
    return parser


def maybe_flip_frame(frame: np.ndarray, flip_frame: bool) -> np.ndarray:
    """Conditionally flip frame horizontally."""
    if flip_frame:
        return cv2.flip(frame, 1)
    return frame


def draw_overlay(
    frame: np.ndarray,
    frame_num: int,
    theta: float | None,
    theta_for_overlay: float | None,
    servo_angle: float,
    servo_center_angle: float,
    fsm_state: str,
    show_guidance_overlay: bool,
    start_calib_threshold_deg: float,
    stop_calib_threshold_deg: float,
    overlay_scale: float = 1.0,
) -> np.ndarray:
    """Render textual/gauge guidance overlay and return annotated frame."""
    output = frame.copy()
    scale = max(0.3, float(overlay_scale))
    thickness = max(1, int(round(scale)))
    cv2.putText(
        output,
        f"frame={frame_num} state={fsm_state}",
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55 * scale,
        (0, 255, 0),
        thickness,
        cv2.LINE_AA,
    )
    cv2.putText(
        output,
        f"theta={'' if theta is None else f'{theta:.2f}'} servo={servo_angle:.2f}",
        (10, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5 * scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )

    if show_guidance_overlay:
        h, w = output.shape[:2]
        center_x = w // 2
        cv2.line(output, (center_x, h - 60), (center_x, h - 10), (0, 255, 255), 1)
        if theta_for_overlay is not None:
            heading_x = int(np.clip((theta_for_overlay / 180.0) * w, 0, w - 1))
            cv2.line(output, (heading_x, h - 70), (heading_x, h - 5), (255, 0, 255), 2)
        cv2.putText(
            output,
            f"start={start_calib_threshold_deg:.1f} stop={stop_calib_threshold_deg:.1f} center={servo_center_angle:.1f}",
            (10, h - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45 * scale,
            (200, 200, 200),
            thickness,
            cv2.LINE_AA,
        )

    return output


def build_detector_debug_panel(frame_width: int, panel_height: int, detector_debug: dict[str, Any]) -> np.ndarray:
    """Build 2x2 detector debug panel from provided stage images."""
    panel_h = max(120, int(panel_height))
    panel_w = max(200, int(frame_width))
    tile_h = panel_h // 2
    tile_w = panel_w // 2

    def to_bgr(value: Any) -> np.ndarray:
        if isinstance(value, np.ndarray) and value.size > 0:
            image = value
        else:
            image = np.zeros((tile_h, tile_w), dtype=np.uint8)
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return cv2.resize(image, (tile_w, tile_h))

    gray = to_bgr(detector_debug.get("gray"))
    edges = to_bgr(detector_debug.get("edges"))
    hough = to_bgr(detector_debug.get("hough_vis"))
    grouped = to_bgr(detector_debug.get("grouped_vis"))

    top = np.hstack((gray, edges))
    bottom = np.hstack((hough, grouped))
    panel = np.vstack((top, bottom))

    lines_count = detector_debug.get("lines_count", "")
    groups_count = detector_debug.get("groups_count", "")
    cv2.putText(
        panel,
        f"lines={lines_count} groups={groups_count}",
        (8, panel.shape[0] - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return panel
