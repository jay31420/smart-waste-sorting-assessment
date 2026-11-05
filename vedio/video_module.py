"""供 YOLO 逐帧处理的视频文件模块骨架。

原比赛代码使用 QMediaPlayer 直接播放视频，画面无法可靠地逐帧交给 YOLO。
本考核保留原 ``vedio`` 目录名，但统一使用 OpenCV 输出 BGR 帧。
"""

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


class VideoFileSource:
    """视频文件输入源。

    打开文件、读取元数据和释放资源的框架已给出。学员需要完成逐帧读取、
    跳转与重新播放，并把进度反馈接入 UI。
    """

    kind = "video"

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError("视频文件不存在：{}".format(self.path))
        self.display_name = str(self.path)
        self.cap = cv2.VideoCapture(str(self.path))
        if not self.cap.isOpened():
            raise RuntimeError("无法打开视频：{}".format(self.path))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.source_fps = float(self.cap.get(cv2.CAP_PROP_FPS))
        self.duration_seconds = (
            self.frame_count / self.source_fps if self.source_fps > 0 else 0.0
        )

    @property
    def current_frame(self) -> int:
        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """TODO 10：读取下一帧，正确处理视频结尾和解码失败。"""
        return False, None

    def seek_frame(self, frame_index: int) -> bool:
        """TODO 11：校验范围并跳转到指定帧。"""
        return False

    def restart(self) -> bool:
        """从第 0 帧重新播放。"""
        return self.seek_frame(0)

    def release(self) -> None:
        self.cap.release()
