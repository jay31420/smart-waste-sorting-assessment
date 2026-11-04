"""Video-file and live-camera frame sources."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


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


class OpenCVFrameSource(FrameSource):
    def __init__(self, source, kind: str) -> None:
        if kind not in ("video", "camera"):
            raise ValueError("图像源只支持 video 或 camera")
        self.kind = kind
        self.source = source
        self.display_name = str(source) if kind == "video" else "摄像头 {}".format(source)
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError("无法打开{}：{}".format("视频" if kind == "video" else "摄像头", source))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if kind == "video" else 0
        self.source_fps = float(self.cap.get(cv2.CAP_PROP_FPS))

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.cap.read()

    def restart(self) -> bool:
        if self.kind != "video":
            return False
        return bool(self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0))

    def release(self) -> None:
        self.cap.release()


def create_frame_source(kind: str, value: str = "") -> FrameSource:
    if kind == "video":
        video_path = Path(value or DEFAULT_VIDEO)
        if not video_path.is_file():
            raise FileNotFoundError("视频文件不存在：{}".format(video_path))
        return OpenCVFrameSource(str(video_path), "video")
    if kind == "camera":
        try:
            camera_index = int(value or 0)
        except ValueError as exc:
            raise ValueError("摄像头编号必须是整数") from exc
        return OpenCVFrameSource(camera_index, "camera")
    raise ValueError("未知图像源：{}；只允许 video 或 camera".format(kind))
