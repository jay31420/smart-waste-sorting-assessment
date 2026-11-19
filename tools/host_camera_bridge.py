"""Expose the Windows webcam as a local JPEG endpoint for the Docker app."""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2


class CameraBridge:
    def __init__(self, camera_index: int, fps: float, jpeg_quality: int) -> None:
        self.camera_index = camera_index
        self.interval = 1.0 / max(1.0, fps)
        self.jpeg_quality = max(30, min(95, jpeg_quality))
        self._frame = None
        self._error = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="host-camera-bridge",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def snapshot(self):
        with self._lock:
            return self._frame, self._error

    def _capture_loop(self) -> None:
        while not self._stop.is_set():
            capture = cv2.VideoCapture(self.camera_index)
            if not capture.isOpened():
                with self._lock:
                    self._frame = None
                    self._error = "无法打开摄像头 {}".format(self.camera_index)
                capture.release()
                self._stop.wait(1.0)
                continue

            failures = 0
            try:
                while not self._stop.is_set() and failures < 8:
                    started = time.monotonic()
                    ok, frame = capture.read()
                    if not ok or frame is None:
                        failures += 1
                        with self._lock:
                            self._frame = None
                            self._error = "摄像头帧读取失败，正在重连"
                        self._stop.wait(0.15)
                        continue
                    failures = 0
                    ok, encoded = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
                    )
                    if ok:
                        with self._lock:
                            self._frame = encoded.tobytes()
                            self._error = None
                    remaining = self.interval - (time.monotonic() - started)
                    if remaining > 0:
                        self._stop.wait(remaining)
            finally:
                capture.release()
            if not self._stop.is_set():
                self._stop.wait(0.5)


class BridgeRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            frame, error = self.server.camera.snapshot()
            if frame is not None:
                error = None
            self._send_json(
                {
                    "ready": frame is not None,
                    "error": error,
                },
                200 if frame is not None else 503,
            )
            return
        if self.path.split("?", 1)[0] == "/frame.jpg":
            frame, error = self.server.camera.snapshot()
            if frame is None:
                self._send_json({"error": error or "摄像头尚未产生画面"}, 503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.end_headers()
            self.wfile.write(frame)
            return
        self._send_json({"error": "not found"}, 404)

    def _send_json(self, payload, status: int) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args) -> None:
        return


def parse_args():
    parser = argparse.ArgumentParser(
        description="将 Windows 摄像头提供为 Docker 可访问的 JPEG 画面源"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8091, type=int)
    parser.add_argument("--camera-index", default=0, type=int)
    parser.add_argument("--fps", default=15.0, type=float)
    parser.add_argument("--jpeg-quality", default=85, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    camera = CameraBridge(
        camera_index=args.camera_index,
        fps=args.fps,
        jpeg_quality=args.jpeg_quality,
    )
    camera.start()
    server = ThreadingHTTPServer((args.host, args.port), BridgeRequestHandler)
    server.daemon_threads = True
    server.camera = camera
    print(
        "Host camera bridge listening on http://{}:{}/frame.jpg".format(
            args.host,
            args.port,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        camera.stop()


if __name__ == "__main__":
    main()
