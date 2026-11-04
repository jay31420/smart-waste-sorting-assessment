"""Background YOLO inference and lower-controller communication worker."""

import threading
import time
from typing import Optional

import cv2
from PyQt5 import QtCore, QtGui

from .controller import SortingController
from .detectors import Detection, YoloDetector
from .frame_sources import FrameSource, create_frame_source
from .protocol import WASTE_NAMES, WasteType
from .transport import SerialTransport, TcpTransport


BOX_COLORS = {
    WasteType.RECYCLABLE: (255, 150, 30),
    WasteType.KITCHEN: (60, 190, 70),
    WasteType.HAZARDOUS: (40, 40, 230),
    WasteType.OTHER: (160, 160, 160),
}
DRAW_WASTE_NAMES = {
    WasteType.RECYCLABLE: "recyclable",
    WasteType.KITCHEN: "kitchen",
    WasteType.HAZARDOUS: "hazardous",
    WasteType.OTHER: "other",
}


class SortingWorker(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QtGui.QImage)
    state_changed = QtCore.pyqtSignal(str)
    counts_changed = QtCore.pyqtSignal(object)
    bins_changed = QtCore.pyqtSignal(object)
    detection_changed = QtCore.pyqtSignal(object)
    model_changed = QtCore.pyqtSignal(str)
    source_changed = QtCore.pyqtSignal(str)
    source_finished = QtCore.pyqtSignal()
    log_message = QtCore.pyqtSignal(str)
    connection_changed = QtCore.pyqtSignal(bool)
    fps_changed = QtCore.pyqtSignal(float)

    def __init__(
        self,
        sim_host: str,
        sim_port: int,
        source_kind: str = "video",
        source_value: str = "assets/assessment_demo.mp4",
        weights: str = "Predict/best.pt",
        confidence: float = 0.50,
        transport_kind: str = "tcp",
        serial_port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.sim_host = sim_host
        self.sim_port = sim_port
        self.source_kind = source_kind
        self.source_value = source_value
        self.weights = weights
        self.confidence = confidence
        self.transport_kind = transport_kind
        self.serial_port = serial_port
        self.baudrate = baudrate
        self._stop_event = threading.Event()
        self._running_event = threading.Event()
        self._settings_lock = threading.Lock()
        self._reset_requested = False
        self._restart_requested = False
        self._source_change = None
        self._controller = None  # type: Optional[SortingController]
        self._source = None  # type: Optional[FrameSource]
        self._detector = None  # type: Optional[YoloDetector]
        self._at_video_end = False

    def prepare_model(self) -> None:
        """Load PyTorch/YOLO before QThread starts.

        On Windows, importing PyTorch for the first time inside a newly-created
        QThread can stall Qt window creation.  Loading once on the GUI thread is
        deterministic; all subsequent inference still runs in this worker.
        """
        if self._detector is not None:
            return
        self.model_changed.emit("正在加载 {} …".format(self.weights))
        self._detector = YoloDetector(
            weights=self.weights,
            confidence=self.confidence,
        )
        self.model_changed.emit("已加载 · {}".format(self._detector.device))

    def start_processing(self) -> None:
        with self._settings_lock:
            if self._at_video_end:
                self._restart_requested = True
        self._running_event.set()

    def pause_processing(self) -> None:
        self._running_event.clear()
        self.state_changed.emit("已暂停")

    def request_reset(self) -> None:
        with self._settings_lock:
            self._reset_requested = True

    def request_source(self, kind: str, value: str = "") -> None:
        with self._settings_lock:
            self._source_change = (kind, value)

    def stop(self) -> None:
        self._stop_event.set()
        self._running_event.set()

    def _event(self, name: str, data: dict) -> None:
        if name == "state":
            self.state_changed.emit(data["value"])
        elif name == "counts":
            self.counts_changed.emit(data["values"])
        elif name == "bins":
            self.bins_changed.emit(data["values"])
        elif name == "log":
            self.log_message.emit(data["message"])
        elif name in ("tx", "rx"):
            self.log_message.emit("{}  {}".format(name.upper(), data["packet"]))

    def _apply_requests(self) -> None:
        with self._settings_lock:
            reset_requested = self._reset_requested
            self._reset_requested = False
            restart_requested = self._restart_requested
            self._restart_requested = False
            source_change = self._source_change
            self._source_change = None

        if reset_requested and self._controller is not None:
            self._controller.reset()
        if source_change is not None:
            try:
                new_source = create_frame_source(*source_change)
            except Exception as exc:
                self.log_message.emit("切换图像源失败：{}".format(exc))
            else:
                old_source, self._source = self._source, new_source
                if old_source is not None:
                    old_source.release()
                self._at_video_end = False
                self.source_changed.emit(new_source.display_name)
                self.detection_changed.emit(None)
                self.log_message.emit("图像源已切换：{}".format(new_source.display_name))
        if restart_requested and self._source is not None:
            if self._source.restart():
                self._at_video_end = False
                self.log_message.emit("视频已从头开始")

    @staticmethod
    def _to_qimage(frame) -> QtGui.QImage:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        return QtGui.QImage(
            rgb.data, width, height, channels * width, QtGui.QImage.Format_RGB888
        ).copy()

    @staticmethod
    def _draw_detections(frame, detections) -> None:
        for detection in detections:
            x1, y1, x2, y2 = detection.box
            color = BOX_COLORS[detection.waste_type]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            label = "{} / {} {:.0f}%".format(
                detection.class_name,
                DRAW_WASTE_NAMES[detection.waste_type],
                detection.confidence * 100,
            )
            cv2.putText(
                frame,
                label,
                (x1, max(26, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.68,
                color,
                2,
                cv2.LINE_AA,
            )

    def run(self) -> None:
        if self.transport_kind == "serial":
            transport = SerialTransport(self.serial_port, self.baudrate)
            connection_name = "串口 {} @ {}".format(self.serial_port, self.baudrate)
        else:
            transport = TcpTransport(self.sim_host, self.sim_port)
            connection_name = "模拟下位机 {}:{}".format(self.sim_host, self.sim_port)

        self._controller = SortingController(transport, self._event)
        last_connect_attempt = 0.0
        frame_times = []
        previous_connection = False

        try:
            if self._detector is None:
                self.prepare_model()
            detector = self._detector
            self.model_changed.emit("已加载 · {}".format(detector.device))
            self.log_message.emit("YOLO 权重加载成功：{} ({})".format(self.weights, detector.device))

            self._source = create_frame_source(self.source_kind, self.source_value)
            self.source_changed.emit(self._source.display_name)
            self.log_message.emit("图像源已打开：{}".format(self._source.display_name))

            while not self._stop_event.is_set():
                now = time.monotonic()
                if not transport.connected and now - last_connect_attempt >= 1.5:
                    last_connect_attempt = now
                    try:
                        transport.connect()
                        self.log_message.emit("{}连接成功".format(connection_name))
                    except Exception as exc:
                        self.log_message.emit("等待{}：{}".format(connection_name, exc))

                if transport.connected != previous_connection:
                    previous_connection = transport.connected
                    self.connection_changed.emit(previous_connection)

                self._apply_requests()
                self._controller.poll()

                if not self._running_event.is_set():
                    self.msleep(40)
                    continue

                ok, frame = self._source.read() if self._source is not None else (False, None)
                if not ok or frame is None:
                    if self._source is not None and self._source.kind == "video":
                        self._at_video_end = True
                        self._running_event.clear()
                        self.detection_changed.emit(None)
                        self.source_finished.emit()
                        self.state_changed.emit("视频播放完成")
                        self.log_message.emit("视频播放完成，再次开始可从头播放")
                    else:
                        self.log_message.emit("摄像头读取失败")
                        self.msleep(200)
                    continue

                started = time.monotonic()
                detections = detector.detect(frame)
                best = detections[0] if detections else None
                self.detection_changed.emit(best)

                # Communication is not faked: only a connected lower controller
                # receives stable YOLO results and confirms completed actions.
                if transport.connected:
                    self._controller.process_detection(best)

                self._draw_detections(frame, detections)
                self.frame_ready.emit(self._to_qimage(frame))

                completed = time.monotonic()
                frame_times.append(completed)
                frame_times = [stamp for stamp in frame_times if completed - stamp <= 1.0]
                self.fps_changed.emit(float(len(frame_times)))

                source_fps = self._source.source_fps if self._source is not None else 0.0
                target_delay = 1.0 / source_fps if source_fps > 1.0 else 0.03
                remaining = target_delay - (completed - started)
                if remaining > 0:
                    self.msleep(int(remaining * 1000))
        except Exception as exc:
            self.model_changed.emit("加载或运行失败")
            self.log_message.emit("工作线程异常：{}".format(exc))
            self.state_changed.emit("运行异常")
        finally:
            if self._source is not None:
                self._source.release()
            transport.close()
            self.connection_changed.emit(False)
