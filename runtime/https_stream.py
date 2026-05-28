"""HTTPS MJPEG streaming utilities backed by a shared frame store."""

from __future__ import annotations

import ipaddress
import json
import ssl
import threading
import time
import urllib.parse
from datetime import datetime, timedelta
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

import cv2


@dataclass
class SharedFrameStore:
    """Thread-safe JPEG/telemetry store for stream server consumers."""

    jpeg_bytes: Optional[bytes] = None
    timestamp_unix: Optional[float] = None
    telemetry: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def set_frame(self, frame_bgr: Any, telemetry: dict[str, Any]) -> None:
        """Encode BGR frame to JPEG and atomically store bytes + telemetry."""
        ok, encoded = cv2.imencode(".jpg", frame_bgr)
        if not ok:
            return
        with self._lock:
            self.jpeg_bytes = bytes(encoded.tobytes())
            self.timestamp_unix = time.time()
            self.telemetry = dict(telemetry)

    def snapshot(self) -> tuple[Optional[bytes], Optional[float], dict[str, Any] | None]:
        """Return a consistent snapshot of frame payload and telemetry."""
        with self._lock:
            payload = None if self.jpeg_bytes is None else bytes(self.jpeg_bytes)
            telemetry = None if self.telemetry is None else dict(self.telemetry)
            return payload, self.timestamp_unix, telemetry


class HttpsMjpegServer:
    """Threaded HTTPS server exposing status/snapshot/stream endpoints."""

    def __init__(
        self,
        host: str,
        port: int,
        stream_path: str,
        snapshot_path: str,
        status_path: str,
        token: str,
        cert_file: str,
        key_file: str,
        frame_store: SharedFrameStore,
    ) -> None:
        self._host = host
        self._port = int(port)
        self._stream_path = self._normalize_path(stream_path)
        self._snapshot_path = self._normalize_path(snapshot_path)
        self._status_path = self._normalize_path(status_path)
        self._token = token
        self._cert_file = cert_file
        self._key_file = key_file
        self._frame_store = frame_store

        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start HTTPS server in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "HttpsMjpegServer/1.0"

            def do_GET(self) -> None:  # noqa: N802
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                if outer._token and params.get("token", [""])[0] != outer._token:
                    self.send_response(HTTPStatus.FORBIDDEN)
                    self.end_headers()
                    return

                if parsed.path == outer._status_path:
                    self._handle_status()
                    return
                if parsed.path == outer._snapshot_path:
                    self._handle_snapshot()
                    return
                if parsed.path == outer._stream_path:
                    self._handle_stream()
                    return
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def _handle_status(self) -> None:
                payload, timestamp_unix, telemetry = outer._frame_store.snapshot()
                body = {
                    "ok": True,
                    "has_frame": payload is not None,
                    "timestamp_unix": timestamp_unix,
                    "telemetry": telemetry,
                }
                data = json.dumps(body).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _handle_snapshot(self) -> None:
                payload, _, _ = outer._frame_store.snapshot()
                if payload is None:
                    self.send_response(HTTPStatus.NO_CONTENT)
                    self.end_headers()
                    return
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _handle_stream(self) -> None:
                boundary = "frame"
                self.send_response(HTTPStatus.OK)
                self.send_header("Age", "0")
                self.send_header("Cache-Control", "no-cache, private")
                self.send_header("Pragma", "no-cache")
                self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary}")
                self.end_headers()
                try:
                    while True:
                        payload, _, _ = outer._frame_store.snapshot()
                        if payload is None:
                            time.sleep(0.05)
                            continue
                        self.wfile.write(f"--{boundary}\r\n".encode("utf-8"))
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
                        self.wfile.write(payload)
                        self.wfile.write(b"\r\n")
                        time.sleep(0.05)
                except (BrokenPipeError, ConnectionResetError):
                    return

        self._server = ThreadingHTTPServer((self._host, self._port), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self._cert_file, self._key_file)
        self._server.socket = context.wrap_socket(self._server.socket, server_side=True)

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background server."""
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def stream_url(self) -> str:
        """Return stream endpoint URL."""
        return f"https://{self._host}:{self._port}{self._stream_path}"

    def status_url(self) -> str:
        """Return status endpoint URL."""
        return f"https://{self._host}:{self._port}{self._status_path}"

    def snapshot_url(self) -> str:
        """Return snapshot endpoint URL."""
        return f"https://{self._host}:{self._port}{self._snapshot_path}"

    @staticmethod
    def _normalize_path(path: str) -> str:
        normalized = path.strip()
        if not normalized.startswith("/"):
            normalized = "/" + normalized
        return normalized


def ensure_self_signed_cert(cert_file: str, key_file: str, host: str, valid_days: int) -> None:
    """Ensure cert+key pair exists; generate self-signed pair when missing."""
    cert_path = Path(cert_file)
    key_path = Path(key_file)
    if cert_path.exists() and key_path.exists() and cert_path.stat().st_size > 0 and key_path.stat().st_size > 0:
        return

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UOG AIS"),
        x509.NameAttribute(NameOID.COMMON_NAME, host),
    ])

    san_name: x509.GeneralName
    try:
        san_name = x509.IPAddress(ipaddress.ip_address(host))
    except ValueError:
        san_name = x509.DNSName(host)

    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=max(1, int(valid_days))))
        .add_extension(x509.SubjectAlternativeName([san_name]), critical=False)
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
