# Unified Calibration Module

Unified Calibration is a single runtime module that detects lane geometry, computes safe steering from vanishing-point math, and publishes telemetry/debug outputs for analysis.

## What It Does

- Runs a continuous camera loop through `UnifiedCalibrator`.
- Extracts line segments in a top ROI and selects opposite-slope lane candidates.
- Computes vanishing point + bottom intercepts.
- Applies a 3-stage steering governor with safety-first behavior.
- Logs telemetry, renders overlays, and can publish HTTPS MJPEG frames.

## 3-Stage Vanishing Point Logic

1. **Vision Lost (Gapping)**
   - Trigger: no valid geometric pair / VP unavailable.
   - Action: hold neutral steering (`90.0°`).
2. **Danger Zone Override**
   - Trigger: bottom intercepts violate `DANGER_MARGIN_PX` boundaries.
   - Action: bypass PD and apply fixed nudge `±DANGER_NUDGE_DEG`.
3. **Tracking (Hysteresis + PD)**
   - Trigger: geometry valid and safe margins respected.
   - Action: map VP to angle, apply hysteresis (`VP_INNER_THRESH`, `VP_OUTER_THRESH`), then PD correction.

---

## Setup

### 1) Create runtime environment file

```bash
cp .env.template .env
```

### 2) Tune `.env` for your camera and lane scene

Start with defaults, then tune conservatively (small changes, one group at a time).

### 3) Run

```bash
python main.py
```

Press `Ctrl+C` for graceful shutdown.

---

## Tuning Guide (Practical)

Tune in this order to reduce instability:

### A. Camera + Loop

- `MAIN_CAMERA_INDEX`: correct physical camera device.
- `MAIN_TARGET_HZ`: stable loop rate (start at `30.0`).
- `MAIN_FLIP_FRAME`: set `true` only if image is mirrored.

If steering feels delayed, verify camera FPS and reduce expensive debug features first.

### B. Vision Detection Robustness

- `ROI_HEIGHT_PCT`: how much upper frame is processed (default `0.6`).
- `VISION_CANNY_LOW/HIGH`: edge sensitivity.
- `VISION_HOUGH_THRESHOLD`, `VISION_HOUGH_MIN_LINE_LENGTH`, `VISION_HOUGH_MAX_LINE_GAP`.
- `VISION_MIN_ABS_SLOPE`: rejects near-horizontal lines.

Tips:
- Too many noisy lines -> increase `VISION_HOUGH_THRESHOLD` or `VISION_MIN_ABS_SLOPE`.
- Missing lines -> lower `VISION_HOUGH_THRESHOLD` or `VISION_CANNY_LOW` slightly.

### C. Safety Margins

- `DANGER_MARGIN_PX`: boundary guard width from left/right frame edges.
- `DANGER_NUDGE_DEG`: fixed correction applied in danger override.

Tips:
- Frequent danger state in normal lane center -> reduce `DANGER_MARGIN_PX`.
- Recovery too weak -> increase `DANGER_NUDGE_DEG` gradually.

### D. Tracking Stability

- `VP_INNER_THRESH`: neutral deadband around center.
- `VP_OUTER_THRESH`: activate tracking when error is large enough.
- `PID_KP`, `PID_KD`: responsiveness and damping.

Tips:
- Oscillation -> reduce `PID_KP` or increase `PID_KD` slightly.
- Too slow to align -> increase `PID_KP` in small steps.
- Chattering around center -> increase `VP_INNER_THRESH` slightly.

---

## Small Demo Workflow

Use this quick bench test before road/track testing:

1. Keep robot stationary and point camera at a lane-like corridor.
2. Enable overlay:
   - `MAIN_SHOW_GUIDANCE_OVERLAY=true`
   - `MAIN_DEBUG_MODE=true`
3. Run `python main.py`.
4. Confirm overlay markers:
   - VP marker appears near line intersection.
   - Two bottom intercept markers appear near frame bottom.
   - Red vertical danger boundaries appear at both margins.
5. Move camera view left/right slightly:
   - Near-center scene should hold around neutral steering.
   - Large deviation should enter tracking PD.
   - Boundary crossings should trigger danger override.

Expected result: smooth transitions between **GAPPING**, **DANGER_LEFT/RIGHT**, and **TRACKING_COAST/PD** without violent oscillation.

---

## Debug and Output

- CSV logging: `MAIN_CSV_LOG_FILE` (saved as `logs/<day_month_year>/<hour_minute>_<name>.csv`)
- Debug visualizer (when `MAIN_DEBUG_MODE=true`): `MAIN_DEBUG_VISUALIZER=imshow|video|both`
- Debug video output path/fps: `MAIN_DEBUG_VIDEO_OUTPUT`, `MAIN_VIDEO_OUTPUT_FPS`
- Legacy toggles remain available: `MAIN_SHOW_PREVIEW`, `MAIN_WRITE_DEBUG_VIDEO`
- HTTPS stream: enable `MAIN_HTTPS_STREAM_ENABLED` and configure `MAIN_HTTPS_*`

For first deployment, keep streaming and video writing disabled until core tracking is stable.

---

## Utility API Documentation

The codebase now includes implementation docs for the reusable utility API surface:

- `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/docs/unified_calibration_components.md`
- `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/docs/runtime_video_runtime_helpers.md`
- `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/docs/runtime_https_stream.md`
- `/tmp/workspace/NhatNam041206/UOG_AIS_AUTOBOT_CALIBRATION_V2/docs/vision_detector.md`
