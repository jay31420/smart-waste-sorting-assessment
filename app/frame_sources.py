"""统一创建视频文件和实时摄像头输入源。"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

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


def create_frame_source(kind: str, value: str = "") -> FrameSource:
    if kind == "video":
        return VideoFileSource(value or DEFAULT_VIDEO)
    if kind == "camera":
        try:
            camera_index = int(value or 0)
        except ValueError as exc:
            raise ValueError("摄像头编号必须是整数") from exc
        return CameraFrameSource(camera_index)
    raise ValueError("未知图像源：{}；只允许 video 或 camera".format(kind))
