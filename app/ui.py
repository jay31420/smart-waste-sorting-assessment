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
        header.addWidget(self.state_label)
        header.addWidget(QtWidgets.QLabel("下位机："))
        self.connection_label = QtWidgets.QLabel("未连接")
        self.connection_label.setMinimumWidth(75)
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
        self.camera_label = QtWidgets.QLabel("导入视频或打开摄像头，然后点击“开始识别”")
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_label.setMinimumSize(760, 470)
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

        controls = QtWidgets.QGroupBox("运行控制（布局与视觉样式由学员继续优化）")
        controls_layout = QtWidgets.QHBoxLayout(controls)
        self.video_button = QtWidgets.QPushButton("导入视频")
        self.camera_button = QtWidgets.QPushButton("打开摄像头")
        self.start_button = QtWidgets.QPushButton("开始识别")
        self.reset_button = QtWidgets.QPushButton("重置统计")
        self.quit_button = QtWidgets.QPushButton("退出")
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.camera_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.quit_button)
        root.addWidget(controls)

        # The UI is complete but intentionally restrained: visual hierarchy,
        # responsive layout and interaction polish remain assessment work.
        self.setStyleSheet(
            "QMainWindow { background: #f4f5f7; }"
            "QGroupBox { font-weight: bold; margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; }"
            "QPushButton { min-width: 105px; min-height: 34px; }"
            "QPlainTextEdit { background: white; font-family: Consolas, monospace; }"
            "#titleLabel { color: #263238; }"
        )

    def _connect_signals(self) -> None:
        self.video_button.clicked.connect(self.import_video)
        self.camera_button.clicked.connect(self.open_camera)
        self.start_button.clicked.connect(self.toggle_processing)
        self.reset_button.clicked.connect(self.worker.request_reset)
        self.quit_button.clicked.connect(self.close)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.state_changed.connect(self.state_label.setText)
        self.worker.counts_changed.connect(self.update_counts)
        self.worker.bins_changed.connect(self.update_bins)
        self.worker.detection_changed.connect(self.update_detection)
        self.worker.model_changed.connect(self.model_label.setText)
        self.worker.source_changed.connect(self.source_label.setText)
        self.worker.source_finished.connect(self.on_source_finished)
        self.worker.log_message.connect(self.append_log)
        self.worker.connection_changed.connect(self.update_connection)
        self.worker.fps_changed.connect(lambda value: self.fps_label.setText("{:.0f}".format(value)))

    @QtCore.pyqtSlot()
    def import_video(self) -> None:
        """TODO 8：弹出视频选择框并调用 worker.request_source。"""
        self.append_log("TODO：请完成视频导入功能")

    @QtCore.pyqtSlot()
    def open_camera(self) -> None:
        """TODO 9：选择/打开摄像头并调用 worker.request_source。"""
        self.append_log("TODO：请完成摄像头输入功能")

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
        self.connection_label.setStyleSheet("color: #2e7d32;" if connected else "color: #c62828;")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.worker.stop()
        if not self.worker.wait(5000):
            self.append_log("工作线程未在规定时间内退出")
        event.accept()
