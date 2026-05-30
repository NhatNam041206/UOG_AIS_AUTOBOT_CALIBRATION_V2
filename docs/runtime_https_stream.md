# HTTPS MJPEG Stream API

Module: `runtime/https_stream.py`

## Shared Frame Store

- `@dataclass SharedFrameStore`
  - `set_frame(frame_bgr: Any, telemetry: dict[str, Any]) -> None`
  - `snapshot() -> tuple[Optional[bytes], Optional[float], dict[str, Any] | None]`

## HTTPS Server

- `class HttpsMjpegServer`
  - `start() -> None`
  - `stop() -> None`
  - `stream_url() -> str`
  - `status_url() -> str`
  - `snapshot_url() -> str`

Endpoints are configured via constructor paths (`stream_path`, `snapshot_path`, `status_path`) and optional query token auth.

## TLS Helper

- `ensure_self_signed_cert(cert_file: str, key_file: str, host: str, valid_days: int) -> None`

This function creates a self-signed certificate pair using `cryptography` when cert/key files are missing.
