"""Intentionally plain PyQt UI for the student assessment."""

import datetime
from pathlib import Path
from typing import Dict

from PyQt5 import QtCore, QtGui, QtWidgets

from .detectors import Detection
from .protocol import WASTE_NAMES, WasteType
from .worker import SortingWorker


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, worker: SortingWorker, auto_start: bool = False) -> None:
        super().__init__()
        self.worker = worker
        self._processing = False
        self._scrubbing = False
        self._seek_target = None
        self._video_frame_count = 0
        self._video_fps = 0.0
        self.count_labels = {}  # type: Dict[str, QtWidgets.QLabel]
        self.bin_labels = {}  # type: Dict[str, QtWidgets.QLabel]
        self._build_ui()
        self._connect_signals()
        self._auto_start = auto_start
        QtCore.QTimer.singleShot(50, self._initialize_worker)

    @QtCore.pyqtSlot()
    def _initialize_worker(self) -> None:
        try:
            self.worker.prepare_model()
        except Exception as exc:
            self.model_label.setText("加载失败")
            self.state_label.setText("运行异常")
            self.append_log("YOLO 模型加载失败：{}".format(exc))
            self.start_button.setEnabled(False)
            return
        self.worker.start()
        if self._auto_start:
            QtCore.QTimer.singleShot(500, self.toggle_processing)

    def _build_ui(self) -> None:
        self.setWindowTitle("智能垃圾分拣系统 · 招新考核")
        self.resize(1280, 820)
        self.setMinimumSize(960, 680)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("智能垃圾分拣上位机")
        title.setObjectName("titleLabel")
        title.setFont(QtGui.QFont("Microsoft YaHei", 18, QtGui.QFont.Bold))
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QtWidgets.QLabel("系统状态："))
        self.state_label = QtWidgets.QLabel("等待启动")
        self.state_label.setMinimumWidth(130)
        self.state_label.setObjectName("stateLabel")
        header.addWidget(self.state_label)
        header.addWidget(QtWidgets.QLabel("下位机："))
        self.connection_label = QtWidgets.QLabel("未连接")
        self.connection_label.setMinimumWidth(75)
        self.connection_label.setObjectName("connectionLabel")
        header.addWidget(self.connection_label)
        header.addWidget(QtWidgets.QLabel("FPS："))
        self.fps_label = QtWidgets.QLabel("0")
        self.fps_label.setMinimumWidth(35)
        header.addWidget(self.fps_label)
        root.addLayout(header)

        status_group = QtWidgets.QGroupBox("输入与模型")
        status_layout = QtWidgets.QGridLayout(status_group)
        status_layout.addWidget(QtWidgets.QLabel("当前输入"), 0, 0)
        self.source_label = QtWidgets.QLabel("正在打开默认考核视频…")
        self.source_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        status_layout.addWidget(self.source_label, 0, 1)
        status_layout.addWidget(QtWidgets.QLabel("YOLO 模型"), 1, 0)
        self.model_label = QtWidgets.QLabel("等待加载…")
        status_layout.addWidget(self.model_label, 1, 1)
        root.addWidget(status_group)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        vision_group = QtWidgets.QGroupBox("目标检测画面")
        vision_layout = QtWidgets.QVBoxLayout(vision_group)
        self.camera_label = QtWidgets.QLabel("等待图像源")
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_label.setMinimumSize(400, 300)
        self.camera_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.camera_label.setFrameShape(QtWidgets.QFrame.Box)
        vision_layout.addWidget(self.camera_label)
        splitter.addWidget(vision_group)

        information = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(information)

        result_group = QtWidgets.QGroupBox("当前 YOLO 识别结果")
        result_layout = QtWidgets.QFormLayout(result_group)
        self.class_label = QtWidgets.QLabel("—")
        self.waste_label = QtWidgets.QLabel("—")
        self.confidence_label = QtWidgets.QLabel("—")
        result_layout.addRow("模型类别", self.class_label)
        result_layout.addRow("垃圾分类", self.waste_label)
        result_layout.addRow("置信度", self.confidence_label)
        info_layout.addWidget(result_group)

        stats_group = QtWidgets.QGroupBox("下位机确认后的分类统计")
        stats_layout = QtWidgets.QGridLayout(stats_group)
        stats_layout.addWidget(QtWidgets.QLabel("垃圾类别"), 0, 0)
        stats_layout.addWidget(QtWidgets.QLabel("数量"), 0, 1)
        stats_layout.addWidget(QtWidgets.QLabel("桶状态"), 0, 2)
        for row, waste_type in enumerate(
            (WasteType.RECYCLABLE, WasteType.KITCHEN, WasteType.HAZARDOUS, WasteType.OTHER),
            start=1,
        ):
            name = WASTE_NAMES[waste_type]
            stats_layout.addWidget(QtWidgets.QLabel(name), row, 0)
            count = QtWidgets.QLabel("0")
            count.setAlignment(QtCore.Qt.AlignCenter)
            status = QtWidgets.QLabel("正常")
            status.setAlignment(QtCore.Qt.AlignCenter)
            self.count_labels[name] = count
            self.bin_labels[name] = status
            stats_layout.addWidget(count, row, 1)
            stats_layout.addWidget(status, row, 2)
        info_layout.addWidget(stats_group)

        communication_group = QtWidgets.QGroupBox("下位机通信日志（TX / RX）")
        communication_layout = QtWidgets.QVBoxLayout(communication_group)
        self.log_browser = QtWidgets.QPlainTextEdit()
        self.log_browser.setReadOnly(True)
        self.log_browser.setMaximumBlockCount(500)
        communication_layout.addWidget(self.log_browser)
        info_layout.addWidget(communication_group, 1)
        splitter.addWidget(information)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        progress_layout = QtWidgets.QHBoxLayout()
        self.time_label = QtWidgets.QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(112)
        self.progress_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setToolTip("拖动后跳转到对应视频位置")
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress_slider, 1)
        root.addLayout(progress_layout)

        controls = QtWidgets.QGroupBox("运行控制")
        controls_layout = QtWidgets.QHBoxLayout(controls)
        self.video_button = QtWidgets.QPushButton("导入视频")
        self.camera_button = QtWidgets.QPushButton("打开摄像头")
        self.start_button = QtWidgets.QPushButton("开始识别")
        self.start_button.setObjectName("primaryButton")
        self.reset_button = QtWidgets.QPushButton("重置统计")
        self.reset_button.setObjectName("secondaryButton")
        self.quit_button = QtWidgets.QPushButton("退出")
        self.quit_button.setObjectName("quitButton")
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.camera_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.quit_button)
        root.addWidget(controls)

        self.setStyleSheet(
            "QMainWindow { background: #edf2f3; }"
            "QWidget { color: #263638; font-family: 'Microsoft YaHei'; font-size: 10pt; }"
            "QGroupBox { background: #ffffff; border: 1px solid #d3dddf; border-radius: 5px; "
            "font-weight: 600; margin-top: 10px; padding: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #344b4c; }"
            "QPushButton { background: #ffffff; border: 1px solid #c6d2d4; border-radius: 4px; "
            "min-width: 98px; min-height: 34px; padding: 0 10px; }"
            "QPushButton:hover { background: #e8f3f1; border-color: #16877b; }"
            "QPushButton:pressed { background: #d5e8e5; }"
            "QPushButton#primaryButton { background: #087f73; color: #ffffff; border-color: #087f73; font-weight: 600; }"
            "QPushButton#primaryButton:hover { background: #066d63; }"
            "QPushButton#quitButton:hover { background: #fff0ee; border-color: #c45145; color: #a53d33; }"
            "QPlainTextEdit { background: #fbfcfc; border: 1px solid #d6dfe1; "
            "font-family: Consolas, monospace; font-size: 9pt; }"
            "QLabel#titleLabel { color: #163f3d; }"
            "QLabel#stateLabel, QLabel#connectionLabel { background: #e7eeee; border-radius: 3px; padding: 3px 6px; }"
            "QSlider::groove:horizontal { height: 5px; background: #d6e0e1; border-radius: 2px; }"
            "QSlider::sub-page:horizontal { background: #16877b; border-radius: 2px; }"
            "QSlider::handle:horizontal { width: 13px; margin: -5px 0; border-radius: 6px; background: #087f73; }"
        )

    def _connect_signals(self) -> None:
        self.video_button.clicked.connect(self.import_video)
        self.camera_button.clicked.connect(self.open_camera)
        self.start_button.clicked.connect(self.toggle_processing)
        self.reset_button.clicked.connect(self.worker.request_reset)
        self.quit_button.clicked.connect(self.close)
        self.progress_slider.sliderPressed.connect(self.begin_scrubbing)
        self.progress_slider.sliderReleased.connect(self.seek_video)
        self.progress_slider.valueChanged.connect(self.update_scrub_time)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.state_changed.connect(self.update_state)
        self.worker.counts_changed.connect(self.update_counts)
        self.worker.bins_changed.connect(self.update_bins)
        self.worker.detection_changed.connect(self.update_detection)
        self.worker.model_changed.connect(self.model_label.setText)
        self.worker.source_changed.connect(self.update_source)
        self.worker.source_finished.connect(self.on_source_finished)
        self.worker.log_message.connect(self.append_log)
        self.worker.connection_changed.connect(self.update_connection)
        self.worker.fps_changed.connect(lambda value: self.fps_label.setText("{:.0f}".format(value)))
        self.worker.progress_changed.connect(self.update_progress)

    @QtCore.pyqtSlot()
    def import_video(self) -> None:
        """选择视频文件并请求后台线程切换输入源。"""
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择视频",
            str(Path.cwd()),
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;所有文件 (*)",
        )
        if path:
            self.worker.request_source("video", path)

    @QtCore.pyqtSlot()
    def open_camera(self) -> None:
        """选择摄像头编号并请求后台线程切换输入源。"""
        camera_index, accepted = QtWidgets.QInputDialog.getInt(
            self,
            "打开摄像头",
            "摄像头编号",
            0,
            0,
            16,
            1,
        )
        if accepted:
            self.worker.request_source("camera", str(camera_index))

    @QtCore.pyqtSlot()
    def seek_video(self) -> None:
        if self.progress_slider.isEnabled():
            self._seek_target = self.progress_slider.value()
            self._scrubbing = True
            self.worker.request_seek_frame(self._seek_target)
        else:
            self._scrubbing = False
            self._seek_target = None

    @QtCore.pyqtSlot()
    def begin_scrubbing(self) -> None:
        self._scrubbing = True

    @QtCore.pyqtSlot(int, int, float)
    def update_progress(self, frame_index: int, frame_count: int, fps: float) -> None:
        enabled = frame_count > 0 and fps > 0
        self._video_frame_count = frame_count if enabled else 0
        self._video_fps = fps if enabled else 0.0
        self.progress_slider.setEnabled(enabled)
        self.progress_slider.blockSignals(True)
        if enabled:
            self.progress_slider.setRange(0, max(0, frame_count - 1))
            if self._seek_target is not None and frame_index == self._seek_target:
                self._seek_target = None
                self._scrubbing = False
            if self._scrubbing:
                self.progress_slider.setValue(self.progress_slider.value())
                shown_frame = self.progress_slider.value()
            else:
                self.progress_slider.setValue(min(frame_index, frame_count - 1))
                shown_frame = frame_index
            current_seconds = max(0, shown_frame) / fps
            total_seconds = frame_count / fps
            self.time_label.setText(
                "{} / {}".format(self._format_time(current_seconds), self._format_time(total_seconds))
            )
        else:
            self._seek_target = None
            self._scrubbing = False
            self.progress_slider.setRange(0, 0)
            self.time_label.setText("实时输入")
        self.progress_slider.blockSignals(False)

    @QtCore.pyqtSlot(int)
    def update_scrub_time(self, frame_index: int) -> None:
        if self._scrubbing and self._video_fps > 0:
            self.time_label.setText(
                "{} / {}".format(
                    self._format_time(frame_index / self._video_fps),
                    self._format_time(self._video_frame_count / self._video_fps),
                )
            )

    @QtCore.pyqtSlot(str)
    def update_source(self, name: str) -> None:
        self.source_label.setText(name)
        self._scrubbing = False
        self._seek_target = None
        if not self._processing:
            self.start_button.setText("开始识别")

    @staticmethod
    def _format_time(seconds: float) -> str:
        seconds = max(0, int(seconds))
        return "{:02d}:{:02d}".format(seconds // 60, seconds % 60)

    def _set_processing(self, enabled: bool) -> None:
        self._processing = enabled
        if enabled:
            self.worker.start_processing()
            self.start_button.setText("暂停识别")
        else:
            self.worker.pause_processing()
            self.start_button.setText("开始识别")

    @QtCore.pyqtSlot()
    def toggle_processing(self) -> None:
        self._set_processing(not self._processing)
        self.append_log("视觉识别已{}".format("启动" if self._processing else "暂停"))

    @QtCore.pyqtSlot()
    def on_source_finished(self) -> None:
        self._processing = False
        self.start_button.setText("重新播放")

    @QtCore.pyqtSlot(str)
    def update_state(self, value: str) -> None:
        self.state_label.setText(value)
        if "异常" in value or "失败" in value:
            color = "#a53d33"
            background = "#fff0ee"
        elif "暂停" in value or "完成" in value:
            color = "#7c5a16"
            background = "#fbf2dc"
        elif "执行" in value or "等待下位机" in value:
            color = "#176c88"
            background = "#e5f2f6"
        else:
            color = "#087f73"
            background = "#e3f1ef"
        self.state_label.setStyleSheet("color: {}; background: {};".format(color, background))

    @QtCore.pyqtSlot(QtGui.QImage)
    def update_frame(self, image: QtGui.QImage) -> None:
        pixmap = QtGui.QPixmap.fromImage(image)
        self.camera_label.setPixmap(
            pixmap.scaled(
                self.camera_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )

    @QtCore.pyqtSlot(object)
    def update_detection(self, detection: Detection) -> None:
        if detection is None:
            self.class_label.setText("—")
            self.waste_label.setText("—")
            self.confidence_label.setText("—")
            return
        self.class_label.setText(detection.class_name)
        self.waste_label.setText(WASTE_NAMES[detection.waste_type])
        self.confidence_label.setText("{:.1f}%".format(detection.confidence * 100))

    @QtCore.pyqtSlot(object)
    def update_counts(self, values: dict) -> None:
        for name, value in values.items():
            if name in self.count_labels:
                self.count_labels[name].setText(str(value))

    @QtCore.pyqtSlot(object)
    def update_bins(self, values: dict) -> None:
        for name, is_full in values.items():
            if name in self.bin_labels:
                label = self.bin_labels[name]
                label.setText("满载" if is_full else "正常")
                label.setStyleSheet("color: #c62828;" if is_full else "color: #2e7d32;")

    @QtCore.pyqtSlot(str)
    def append_log(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_browser.appendPlainText("[{}] {}".format(timestamp, message))

    @QtCore.pyqtSlot(bool)
    def update_connection(self, connected: bool) -> None:
        self.connection_label.setText("已连接" if connected else "未连接")
        self.connection_label.setStyleSheet(
            "color: #087f73; background: #e3f1ef;"
            if connected
            else "color: #a53d33; background: #fff0ee;"
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.worker.stop()
        if not self.worker.wait(5000):
            self.append_log("工作线程未在规定时间内退出")
        event.accept()
