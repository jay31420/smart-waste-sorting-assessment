"""统一创建视频文件和实时摄像头输入源。"""

import http.client
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from urllib.parse import urlsplit

import cv2
import numpy as np

from vedio.video_module import VideoFileSource


DEFAULT_VIDEO = "assets/assessment_demo.mp4"


class FrameSource(ABC):
    kind = "unknown"
    display_name = "未知图像源"

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        raise NotImplementedError


class CameraFrameSource(FrameSource):
    kind = "camera"

    def __init__(self, camera_index: int) -> None:
        self.source = camera_index
        self.display_name = "摄像头 {}".format(camera_index)
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("无法打开摄像头：{}".format(camera_index))
        self.frame_count = 0
        self.source_fps = float(self.cap.get(cv2.CAP_PROP_FPS))

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.cap.read()

    def restart(self) -> bool:
        return False

    def release(self) -> None:
        self.cap.release()


class HttpCameraSource(FrameSource):
    """Read the latest JPEG frame from the host-side camera bridge."""

    kind = "camera"

    def __init__(self, url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("摄像头桥地址无效")
        self.source = url
        self.display_name = "宿主机摄像头桥"
        self.frame_count = 0
        self.source_fps = 15.0
        self._host = parsed.hostname
        self._port = parsed.port
        self._path = parsed.path or "/frame.jpg"
        if parsed.query:
            self._path += "?" + parsed.query
        self._secure = parsed.scheme == "https"
        self._connection = None
        self._pending_frame = None
        ok, frame = self._fetch()
        if not ok or frame is None:
            raise RuntimeError("无法连接宿主机摄像头桥：{}".format(url))
        self._pending_frame = frame

    def _fetch(self):
        try:
            if self._connection is None:
                connection_type = (
                    http.client.HTTPSConnection
                    if self._secure
                    else http.client.HTTPConnection
                )
                self._connection = connection_type(
                    self._host,
                    self._port,
                    timeout=2.0,
                )
            self._connection.request(
                "GET",
                self._path,
                headers={"Cache-Control": "no-cache"},
            )
            response = self._connection.getresponse()
            body = response.read()
            if response.status != 200:
                raise RuntimeError("摄像头桥返回 HTTP {}".format(response.status))
            frame = cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise RuntimeError("摄像头桥返回了无法解码的画面")
            return True, frame
        except Exception:
            self._close_connection()
            return False, None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._pending_frame is not None:
            frame, self._pending_frame = self._pending_frame, None
            self.frame_count += 1
            return True, frame
        ok, frame = self._fetch()
        if ok:
            self.frame_count += 1
        return ok, frame

    def restart(self) -> bool:
        return False

    def release(self) -> None:
        self._close_connection()
        self._pending_frame = None

    def _close_connection(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None


def create_frame_source(kind: str, value: str = "") -> FrameSource:
    if kind == "video":
        return VideoFileSource(value or DEFAULT_VIDEO)
    if kind == "camera":
        if value.startswith(("http://", "https://")):
            return HttpCameraSource(value)
        try:
            camera_index = int(value or 0)
        except ValueError as exc:
            raise ValueError("摄像头编号必须是整数") from exc
        return CameraFrameSource(camera_index)
    raise ValueError("未知图像源：{}；只允许 video 或 camera".format(kind))
