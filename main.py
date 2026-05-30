"""Unified calibration runtime entry point with CLI options."""

from __future__ import annotations

import logging
import os

# Parse CLI options early so they can override environment-backed settings
def _parse_and_apply_args() -> None:
    try:
        from runtime.video_runtime_helpers import build_main_arg_parser
    except Exception:
        return
    parser = build_main_arg_parser()
    args, _ = parser.parse_known_args()
    # Apply selected CLI args into environment so config.settings picks them up
    if args.camera_index is not None:
        os.environ.setdefault("MAIN_CAMERA_INDEX", str(args.camera_index))
    if args.target_hz is not None:
        os.environ.setdefault("MAIN_TARGET_HZ", str(args.target_hz))
    if getattr(args, "flip_frame", False):
        os.environ.setdefault("MAIN_FLIP_FRAME", "true")
    if getattr(args, "csv_log_file", None):
        os.environ.setdefault("MAIN_CSV_LOG_FILE", str(args.csv_log_file))


def main() -> None:
    """Configure logging and run the unified calibrator loop."""
    _parse_and_apply_args()
    # Import runtime after args applied so settings read updated env
    from unified_calibration_components import UnifiedCalibrator

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    calibrator = UnifiedCalibrator()
    try:
        calibrator.run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutdown requested by user (Ctrl+C).")


if __name__ == "__main__":
    main()
