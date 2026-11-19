"""Intentionally plain PyQt UI for the student assessment."""

import datetime
import os
from pathlib import Path
from typing import Dict

from PyQt5 import QtCore, QtGui, QtWidgets

from .audio import AudioFeedback
from .detectors import Detection
from .protocol import WASTE_NAMES, WasteType
from .scene import PaintedLandscape, SceneOverlay
from .worker import SortingWorker


class FeedbackButton(QtWidgets.QPushButton):
    def __init__(self, text, audio, parent=None):
        super().__init__(text, parent)
        self._audio = audio
        self.pressed.connect(self._pressed)

    def _pressed(self):
        self._audio.play_click()


class AudioCheckBox(QtWidgets.QCheckBox):
    """Checkbox with a theme-independent checked indicator."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(27)
        metrics = QtGui.QFontMetrics(self.font())
        self.setMinimumWidth(metrics.horizontalAdvance(text) + 30)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        bounds = self.rect().adjusted(0, 0, -1, -1)
        box_size = 16
        box = QtCore.QRectF(
            1,
            (bounds.height() - box_size) / 2.0,
            box_size,
            box_size,
        )
        enabled = self.isEnabled()
        if self.isChecked():
            border = QtGui.QColor("#c3aa6b")
            fill = QtGui.QColor("#245781")
        else:
            border = QtGui.QColor("#758b81")
            fill = QtGui.QColor("#fdfcf6")
        if not enabled:
            border.setAlpha(120)
            fill.setAlpha(120)

        painter.setPen(QtGui.QPen(border, 2.0))
        painter.setBrush(fill)
        painter.drawRoundedRect(box, 4.0, 4.0)

        if self.isChecked():
            painter.setPen(
                QtGui.QPen(
                    QtGui.QColor("#ffffff"),
                    2.0,
                    QtCore.Qt.SolidLine,
                    QtCore.Qt.RoundCap,
                    QtCore.Qt.RoundJoin,
                )
            )
            path = QtGui.QPainterPath()
            path.moveTo(box.left() + 3.5, box.center().y())
            path.lineTo(box.left() + 7.0, box.bottom() - 4.0)
            path.lineTo(box.right() - 3.0, box.top() + 4.0)
            painter.drawPath(path)

        text_color = self.palette().color(QtGui.QPalette.WindowText)
        if not enabled:
            text_color.setAlpha(130)
        painter.setPen(text_color)
        painter.setFont(self.font())
        painter.drawText(
            bounds.adjusted(box_size + 8, 0, 0, 0),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            self.text(),
        )
        painter.end()


class VideoSelectionDialog(QtWidgets.QFrame):
    selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoPicker")
        self.setFixedSize(560, 310)
        self.hide()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("选择视频")
        title.setObjectName("pickerTitle")
        note = QtWidgets.QLabel(
            "请选择内置视频，或选择 project/media 文件夹中的视频。"
        )
        note.setObjectName("dialogNote")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(note)

        self.video_list = QtWidgets.QListWidget()
        self.video_list.itemDoubleClicked.connect(
            lambda _item: self._accept_current()
        )
        layout.addWidget(self.video_list, 1)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QtWidgets.QPushButton("取消")
        open_button = QtWidgets.QPushButton("打开视频")
        open_button.setObjectName("pickerPrimary")
        cancel_button.clicked.connect(self.hide)
        open_button.clicked.connect(self._accept_current)
        button_row.addWidget(cancel_button)
        button_row.addWidget(open_button)
        layout.addLayout(button_row)

        self._labels = []
        self._paths = {}

        self.setStyleSheet(
            "QFrame#videoPicker { background: #f5f1e3; color: #17365a;"
            " border: 3px solid #17365a; }"
            "QFrame#videoPicker QLabel { color: #17365a;"
            " font-family: 'Microsoft YaHei'; font-size: 10pt; }"
            "QLabel#pickerTitle { font-size: 16pt; font-weight: 700;"
            " padding-bottom: 3px; }"
            "QLabel#dialogNote { color: #4a6a80; padding: 2px; }"
            "QListWidget { background: #fffdf5; color: #17365a;"
            " border: 2px solid #17365a; border-radius: 3px; padding: 5px; }"
            "QListWidget::item { min-height: 32px; padding: 4px 8px; }"
            "QListWidget::item:selected { background: #245781; color: #fff8e6; }"
            "QPushButton { background: #fffdf5; color: #17365a;"
            " border: 1px solid #7894a5; min-width: 92px; min-height: 32px; }"
            "QPushButton:hover { background: #e3ece8; border-color: #17365a; }"
            "QPushButton#pickerPrimary { background: #245781; color: #fff8e6;"
            " border-color: #b39758; }"
        )

    def open_options(self, labels, paths):
        self._labels = list(labels)
        self._paths = dict(zip(labels, paths))
        self.video_list.clear()
        self.video_list.addItems(self._labels)
        self.video_list.setCurrentRow(0)
        parent = self.parentWidget()
        if parent is not None:
            self.move(
                max(12, (parent.width() - self.width()) // 2),
                max(12, (parent.height() - self.height()) // 2),
            )
        self.show()
        self.raise_()
        self.video_list.setFocus()

    def _accept_current(self):
        item = self.video_list.currentItem()
        if item is None:
            return
        path = self._paths.get(item.text())
        if path:
            self.hide()
            self.selected.emit(path)


class SkyReturnButton(FeedbackButton):
    def __init__(self, audio, parent=None):
        super().__init__("点击天空回到郊野", audio, parent)
        self.setMinimumHeight(44)
        self.setMinimumWidth(146)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setText("返回郊野")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        bounds = QtCore.QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(QtGui.QPen(QtGui.QColor("#17365a"), 1.8))
        painter.setBrush(QtGui.QColor("#fbf8eb"))
        painter.drawRect(bounds)
        painter.setPen(QtGui.QPen(QtGui.QColor("#b39758"), 0.8))
        painter.drawRect(bounds.adjusted(4, 4, -4, -4))
        painter.setPen(QtGui.QPen(QtGui.QColor("#477b9b"), 1.2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(
            QtCore.QRectF(bounds.left() + 11, bounds.center().y() - 7, 14, 14)
        )
        painter.drawLine(
            QtCore.QPointF(bounds.left() + 18, bounds.center().y() - 7),
            QtCore.QPointF(bounds.left() + 18, bounds.center().y() - 14),
        )
        painter.setPen(QtGui.QColor("#17365a"))
        painter.setFont(QtGui.QFont("Microsoft YaHei", 9, QtGui.QFont.DemiBold))
        painter.drawText(
            bounds.adjusted(34, 0, -7, 0),
            QtCore.Qt.AlignCenter,
            self.text(),
        )
        painter.end()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, worker: SortingWorker, auto_start: bool = False) -> None:
        super().__init__()
        self.worker = worker
        self._processing = False
        self._closing = False
        self._scrubbing = False
        self._seek_target = None
        self._video_frame_count = 0
        self._video_fps = 0.0
        self._settings = QtCore.QSettings("NWPU", "SmartWasteSorting")
        self.audio = AudioFeedback(self)
        self._click_sound_enabled = self._settings.value("audio/click", True, type=bool)
        self._music_enabled = self._settings.value("audio/music", False, type=bool)
        self.audio.set_click_enabled(self._click_sound_enabled)
        self.audio.set_music_enabled(self._music_enabled)
        self._click_toggles = []
        self._music_toggles = []
        self.count_labels = {}  # type: Dict[str, QtWidgets.QLabel]
        self.bin_labels = {}  # type: Dict[str, QtWidgets.QLabel]
        self._build_ui()
        self._connect_signals()
        self._auto_start = auto_start
        self._worker_ready = False
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
        self._worker_ready = True
        if self._auto_start:
            QtCore.QTimer.singleShot(500, self.enter_workspace)

    def _build_ui(self) -> None:
        self.setWindowTitle("智能垃圾分拣系统 · 招新考核")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)
        self.pages = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.pages)
        self._build_scene_page()

        self.workspace_page = QtWidgets.QWidget()
        self.pages.addWidget(self.workspace_page)
        self._build_workspace_ui()

    def _build_scene_page(self) -> None:
        self.scene_page = QtWidgets.QWidget()
        scene_stack = QtWidgets.QStackedLayout(self.scene_page)
        scene_stack.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        self.landscape = PaintedLandscape()
        scene_stack.addWidget(self.landscape)

        overlay = SceneOverlay(self.landscape)
        overlay.setStyleSheet("background: transparent;")
        overlay_layout = QtWidgets.QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(18, 16, 18, 16)
        audio_row = QtWidgets.QHBoxLayout()
        audio_row.addStretch(1)
        sound_controls = QtWidgets.QFrame()
        sound_controls.setStyleSheet(
            "QFrame { background: rgba(248, 248, 239, 225); border: 1px solid rgba(65, 92, 82, 90); border-radius: 11px; }"
            "QCheckBox { color: #355853; font-weight: 600; spacing: 7px; padding: 5px 8px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
            "QCheckBox::indicator:checked { background: #c89a57; border: 2px solid #f1dfbb; border-radius: 4px; }"
            "QCheckBox::indicator:unchecked { background: #e5ebe2; border: 2px solid #758b81; border-radius: 4px; }"
        )
        sound_layout = QtWidgets.QHBoxLayout(sound_controls)
        sound_layout.setContentsMargins(4, 2, 4, 2)
        self.scene_click_toggle = self._make_audio_toggle("按键声", self._click_sound_enabled, self._click_toggles)
        self.scene_music_toggle = self._make_audio_toggle(
            "背景音乐《脚踏车》",
            self._music_enabled,
            self._music_toggles,
            available=self.audio.music_available,
        )
        sound_layout.addWidget(self.scene_click_toggle)
        sound_layout.addWidget(self.scene_music_toggle)
        audio_row.addWidget(sound_controls)
        overlay_layout.addLayout(audio_row)
        overlay_layout.addStretch(1)
        scene_stack.addWidget(overlay)
        scene_stack.setCurrentWidget(overlay)
        self.pages.addWidget(self.scene_page)
        self.pages.setCurrentWidget(self.scene_page)

    def _make_audio_toggle(self, label, checked, group, available=None):
        toggle = AudioCheckBox(label)
        if available is None:
            available = self.audio.available
        toggle.setEnabled(available)
        toggle.setChecked(bool(checked) if available else False)
        if not available:
            toggle.setToolTip("当前运行环境没有可用的音频输出设备")
        group.append(toggle)
        return toggle

    def _build_workspace_ui(self) -> None:
        from .workspace import build_workspace

        self.sky_button_factory = SkyReturnButton
        build_workspace(self)
        return

        root = QtWidgets.QVBoxLayout(self.workspace_page)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(9)

        header = QtWidgets.QHBoxLayout()
        self.sky_button = SkyReturnButton(self.audio)
        header.addWidget(self.sky_button)
        title = QtWidgets.QLabel("智能垃圾分拣上位机")
        title.setObjectName("titleLabel")
        title.setFont(QtGui.QFont("Microsoft YaHei", 19, QtGui.QFont.Bold))
        header.addWidget(title)
        header.addStretch(1)
        self.workspace_click_toggle = self._make_audio_toggle("按键声", self._click_sound_enabled, self._click_toggles)
        self.workspace_music_toggle = self._make_audio_toggle("背景音乐", self._music_enabled, self._music_toggles)
        header.addWidget(self.workspace_click_toggle)
        header.addWidget(self.workspace_music_toggle)
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
        self.video_button = FeedbackButton("导入视频", self.audio)
        self.camera_button = FeedbackButton("打开摄像头", self.audio)
        self.start_button = FeedbackButton("开始识别", self.audio)
        self.start_button.setObjectName("primaryButton")
        self.reset_button = FeedbackButton("重置统计", self.audio)
        self.reset_button.setObjectName("secondaryButton")
        self.quit_button = FeedbackButton("退出", self.audio)
        self.quit_button.setObjectName("quitButton")
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.camera_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.quit_button)
        root.addWidget(controls)

        self.setStyleSheet(
            "QMainWindow { background: #dfe9e5; }"
            "QWidget { color: #243538; font-family: 'Microsoft YaHei'; font-size: 10pt; }"
            "QGroupBox { background: #fbf8ee; border: 1px solid #c6d0c2; border-radius: 5px; "
            "font-weight: 600; margin-top: 10px; padding: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #214a4b; }"
            "QPushButton { background: #fffdf4; border: 1px solid #b9c7bd; border-radius: 4px; "
            "min-width: 98px; min-height: 34px; padding: 0 10px; }"
            "QPushButton:hover { background: #e6f3ed; border-color: #31877e; }"
            "QPushButton:pressed { background: #d1e8df; }"
            "QPushButton#primaryButton { background: #176f72; color: #ffffff; border-color: #176f72; font-weight: 600; }"
            "QPushButton#primaryButton:hover { background: #0f5c62; }"
            "QPushButton#quitButton:hover { background: #ffede3; border-color: #c45f49; color: #9e4437; }"
            "QPlainTextEdit { background: #f7f6ed; border: 1px solid #c8d2c8; "
            "font-family: Consolas, monospace; font-size: 9pt; }"
            "QLabel#titleLabel { color: #123f45; }"
            "QLabel#stateLabel, QLabel#connectionLabel { background: #d7e5dc; border-radius: 3px; padding: 3px 6px; }"
            "QSlider::groove:horizontal { height: 5px; background: #c4d0c6; border-radius: 2px; }"
            "QSlider::sub-page:horizontal { background: #2c8b83; border-radius: 2px; }"
            "QSlider::handle:horizontal { width: 13px; margin: -5px 0; border-radius: 6px; background: #dd9950; }"
            "QCheckBox { spacing: 6px; color: #254d50; }"
            "QCheckBox::indicator { width: 15px; height: 15px; }"
        )

    def _connect_signals(self) -> None:
        self.video_button.clicked.connect(self.import_video)
        self.camera_button.clicked.connect(self.open_camera)
        self.start_button.clicked.connect(self.toggle_processing)
        self.reset_button.clicked.connect(self.worker.request_reset)
        self.quit_button.clicked.connect(self.close)
        self.landscape.computer_activated.connect(self.enter_workspace)
        self.sky_button.clicked.connect(self.return_to_scene)
        for toggle in self._click_toggles:
            toggle.toggled.connect(self.set_click_sound_enabled)
        for toggle in self._music_toggles:
            toggle.toggled.connect(self.set_music_enabled)
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
        self.worker.fps_changed.connect(lambda value: self.fps_label.setText("{:.0f} FPS".format(value)))
        self.worker.progress_changed.connect(self.update_progress)

    @QtCore.pyqtSlot()
    def import_video(self) -> None:
        """选择视频文件并请求后台线程切换输入源。"""
        if self.worker.camera_source:
            self._import_docker_video()
            return
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择视频",
            os.environ.get("VIDEO_DIALOG_DIR", str(Path.cwd())),
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;所有文件 (*)",
        )
        if path:
            self._activate_source("video", path)

    def _activate_source(self, kind, value):
        self.worker.request_source(kind, value)
        if not self._processing:
            self._set_processing(True)

    def _import_docker_video(self) -> None:
        base = Path(os.environ.get("VIDEO_DIALOG_DIR", "/host-media"))
        extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
        candidates = [
            ("演示视频", Path.cwd() / "assets" / "assessment_demo.mp4"),
            ("长视频", Path.cwd() / "vedio" / "dep.mp4"),
        ]
        if base.is_dir():
            for path in sorted(base.iterdir(), key=lambda item: item.name.lower()):
                if path.is_file() and path.suffix.lower() in extensions:
                    candidates.append(("宿主文件夹", path))
        labels = [
            "{}  ·  {}".format(group, path.name)
            for group, path in candidates
        ]
        if not hasattr(self, "video_picker"):
            self.video_picker = VideoSelectionDialog(self.workspace_page)
            self.video_picker.selected.connect(
                lambda path: self._activate_source("video", path)
            )
        self.video_picker.open_options(
            labels,
            [str(path) for _group, path in candidates],
        )

    @QtCore.pyqtSlot()
    def open_camera(self) -> None:
        """选择摄像头编号并请求后台线程切换输入源。"""
        if self.worker.camera_source:
            self.append_log("正在连接宿主机摄像头桥")
            self._activate_source("camera", self.worker.camera_source)
            return
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
            self._activate_source("camera", str(camera_index))

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
        self.source_label.setToolTip(name)
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
    def enter_workspace(self) -> None:
        self.pages.setCurrentWidget(self.workspace_page)
        if self._worker_ready and not self._processing:
            self._set_processing(True)
            self.append_log("进入工作台，视觉识别已启动")

    @QtCore.pyqtSlot()
    def return_to_scene(self) -> None:
        self._set_processing(False)
        if hasattr(self, "video_picker"):
            self.video_picker.hide()
        self.pages.setCurrentWidget(self.scene_page)

    @QtCore.pyqtSlot(bool)
    def set_click_sound_enabled(self, enabled: bool) -> None:
        self._click_sound_enabled = bool(enabled)
        self.audio.set_click_enabled(enabled)
        self._settings.setValue("audio/click", self._click_sound_enabled)
        for toggle in self._click_toggles:
            toggle.blockSignals(True)
            toggle.setChecked(self._click_sound_enabled if self.audio.available else False)
            toggle.blockSignals(False)

    @QtCore.pyqtSlot(bool)
    def set_music_enabled(self, enabled: bool) -> None:
        self._music_enabled = bool(enabled)
        self.audio.set_music_enabled(enabled)
        self._settings.setValue("audio/music", self._music_enabled)
        for toggle in self._music_toggles:
            toggle.blockSignals(True)
            toggle.setChecked(
                self._music_enabled if self.audio.music_available else False
            )
            toggle.blockSignals(False)

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
        if self._closing:
            event.accept()
            return
        self._closing = True
        self.setEnabled(False)
        self.setWindowTitle("正在安全关闭识别线程…")
        self.audio.stop()
        self.worker.stop()
        event.ignore()
        if not self._worker_ready or not self.worker.isRunning():
            QtCore.QTimer.singleShot(0, self.close)
            return
        self._shutdown_timer = QtCore.QTimer(self)
        self._shutdown_timer.setInterval(100)
        self._shutdown_timer.timeout.connect(self._finish_shutdown)
        self._shutdown_timer.start()

    @QtCore.pyqtSlot()
    def _finish_shutdown(self) -> None:
        if self.worker.isRunning():
            return
        self._shutdown_timer.stop()
        self.close()
