# Unified Calibration Module

This module provides a single entrypoint for vanishing-point-based steering calibration with conservative safety fallbacks.

## 3-Stage Vanishing Point Logic

1. **Vision Lost (Gapping):** if valid lane geometry is unavailable, steering coasts at 90°.
2. **Danger Zone Override:** if bottom intercepts cross `DANGER_MARGIN_PX`, a fixed nudge (`DANGER_NUDGE_DEG`) is applied for recovery.
3. **Tracking (Hysteresis + PD):** vanishing-point angle tracks with inner/outer hysteresis (`VP_INNER_THRESH`, `VP_OUTER_THRESH`) and PD smoothing.

## Setup

1. Copy the template configuration:
   ```bash
   cp .env.template .env
   ```
2. Adjust values in `.env` for your hardware and camera.

## Run

```bash
python main.py
```

Use **Ctrl+C** to stop safely.
