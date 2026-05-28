"""Unified calibration runtime entry point."""

from __future__ import annotations

import logging

from unified_calibration_components import UnifiedCalibrator


def main() -> None:
    """Configure logging and run the unified calibrator loop."""
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
