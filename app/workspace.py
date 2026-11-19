"""Blue-and-ivory ornamental workstation drawn completely with PyQt."""

import math

from PyQt5 import QtCore, QtGui, QtWidgets

from .protocol import WASTE_NAMES, WasteType


INK = QtGui.QColor("#17365a")
INK_SOFT = QtGui.QColor("#315b7d")
GOLD = QtGui.QColor("#b39758")
PAPER = QtGui.QColor("#f2efe2")
PANEL = QtGui.QColor("#f8f5e9")
LIGHT_BLUE = QtGui.QColor("#dfe9e8")


def _title_font(size, bold=True):
    font = QtGui.QFont("STKaiti", size)
    font.setBold(bold)
    return font


def _draw_flower(painter, center, radius, petal_color, center_color):
    painter.save()
    painter.translate(center)
    for index in range(7):
        painter.save()
        painter.rotate(index * 360.0 / 7.0)
        painter.setPen(QtGui.QPen(petal_color.darker(135), 0.8))
        painter.setBrush(petal_color)
        painter.drawEllipse(
            QtCore.QRectF(
                -radius * 0.23,
                -radius * 0.93,
                radius * 0.46,
                radius * 0.76,
            )
        )
        painter.restore()
    painter.setPen(QtGui.QPen(GOLD.darker(120), 1.0))
    painter.setBrush(center_color)
    painter.drawEllipse(QtCore.QRectF(-radius * 0.25, -radius * 0.25, radius * 0.5, radius * 0.5))
    painter.restore()


def _draw_leaf(painter, x, y, width, height, angle, color):
    painter.save()
    painter.translate(x, y)
    painter.rotate(angle)
    painter.setPen(QtGui.QPen(color.darker(125), 0.8))
    painter.setBrush(color)
    path = QtGui.QPainterPath()
    path.moveTo(0, -height / 2.0)
    path.cubicTo(width * 0.7, -height * 0.2, width * 0.7, height * 0.2, 0, height / 2.0)
    path.cubicTo(-width * 0.7, height * 0.2, -width * 0.7, -height * 0.2, 0, -height / 2.0)
    painter.drawPath(path)
    painter.restore()


def _draw_corner_scroll(painter, rect, flip_x=False, flip_y=False):
    painter.save()
    painter.translate(
        rect.right() if flip_x else rect.left(),
        rect.bottom() if flip_y else rect.top(),
    )
    painter.scale(-1 if flip_x else 1, -1 if flip_y else 1)
    pen = QtGui.QPen(QtGui.QColor("#32678d"), 1.7)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)
    path = QtGui.QPainterPath()
    path.moveTo(18, 3)
    path.cubicTo(5, 7, 4, 17, 14, 18)
    path.cubicTo(26, 20, 26, 8, 18, 8)
    path.cubicTo(12, 8, 11, 14, 17, 14)
    painter.drawPath(path)
    path = QtGui.QPainterPath()
    path.moveTo(7, 5)
    path.cubicTo(19, -2, 38, 4, 48, 14)
    painter.drawPath(path)
    painter.restore()


class OrnamentalBackdrop(QtWidgets.QWidget):
    """Paint the aged paper, double frame and floral borders."""

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

        gradient = QtGui.QLinearGradient(self.rect().topLeft(), self.rect().bottomRight())
        gradient.setColorAt(0.0, QtGui.QColor("#f7f3e6"))
        gradient.setColorAt(0.45, QtGui.QColor("#e8eeea"))
        gradient.setColorAt(1.0, QtGui.QColor("#d8e4e3"))
        painter.fillRect(self.rect(), gradient)

        painter.setOpacity(0.16)
        painter.setPen(QtGui.QPen(QtGui.QColor("#718795"), 0.55))
        width = self.width()
        height = self.height()
        for offset in range(30, max(width, height), 70):
            painter.drawLine(offset, 8, offset - 38, height - 8)
            painter.drawLine(8, offset, width - 8, offset - 24)
        painter.setOpacity(1.0)

        outer = QtCore.QRectF(self.rect()).adjusted(7, 7, -7, -7)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(INK, 5.0))
        painter.drawRect(outer)
        painter.setPen(QtGui.QPen(GOLD, 1.2))
        painter.drawRect(outer.adjusted(7, 7, -7, -7))

        for x in (29, width - 34):
            painter.setPen(QtGui.QPen(QtGui.QColor("#6c91a9"), 1.0))
            painter.drawLine(x, 72, x, height - 72)
            painter.setPen(QtGui.QPen(GOLD, 0.8))
            painter.drawLine(x + 5, 86, x + 5, height - 86)

        for y in (86, height // 2 - 34, height - 128):
            _draw_leaf(painter, 34, y + 48, 18, 36, 24, QtGui.QColor("#7896a5"))
            _draw_leaf(painter, width - 35, y + 48, 18, 36, -24, QtGui.QColor("#7896a5"))
        for y, blue in ((122, True), (height // 2, False), (height - 120, True)):
            _draw_flower(
                painter,
                QtCore.QPointF(34, y),
                22 if blue else 25,
                QtGui.QColor("#759cb8") if blue else QtGui.QColor("#f9f7ed"),
                GOLD,
            )
            _draw_flower(
                painter,
                QtCore.QPointF(width - 35, y),
                25 if blue else 22,
                QtGui.QColor("#f9f7ed") if blue else QtGui.QColor("#759cb8"),
                GOLD,
            )

        _draw_corner_scroll(painter, outer.adjusted(10, 10, -10, -10))
        _draw_corner_scroll(painter, outer.adjusted(10, 10, -10, -10), flip_x=True)
        _draw_corner_scroll(painter, outer.adjusted(10, 10, -10, -10), flip_y=True)
        _draw_corner_scroll(painter, outer.adjusted(10, 10, -10, -10), True, True)
        painter.end()


class OrnamentalPanel(QtWidgets.QFrame):
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        bounds = QtCore.QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setBrush(QtGui.QColor(249, 247, 237, 244))
        painter.setPen(QtGui.QPen(INK, 1.8))
        painter.drawRect(bounds)
        painter.setPen(QtGui.QPen(QtGui.QColor("#6e8da1"), 0.8))
        painter.drawRect(bounds.adjusted(4, 4, -4, -4))
        _draw_corner_scroll(painter, bounds.adjusted(5, 5, -5, -5))
        _draw_corner_scroll(painter, bounds.adjusted(5, 5, -5, -5), flip_x=True)
        _draw_corner_scroll(painter, bounds.adjusted(5, 5, -5, -5), flip_y=True)
        _draw_corner_scroll(painter, bounds.adjusted(5, 5, -5, -5), True, True)
        painter.end()


class WorkspaceButton(QtWidgets.QPushButton):
    def __init__(self, text, audio, parent=None):
        super().__init__(text, parent)
        self._audio = audio
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMinimumSize(104, 42)
        self.pressed.connect(self._audio.play_click)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        bounds = QtCore.QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        primary = self.objectName() == "primaryButton"
        hovered = self.underMouse() and self.isEnabled()
        if primary:
            fill = QtGui.QColor("#214f82") if hovered else QtGui.QColor("#173f70")
            text = QtGui.QColor("#f8f4e4")
        else:
            fill = QtGui.QColor("#fbf8eb") if not hovered else QtGui.QColor("#e2ece9")
            text = INK
        if self.objectName() == "quitButton" and hovered:
            fill = QtGui.QColor("#f6e2d7")

        gradient = QtGui.QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
        gradient.setColorAt(0.0, fill.lighter(107))
        gradient.setColorAt(1.0, fill.darker(105))
        painter.setBrush(gradient)
        painter.setPen(QtGui.QPen(INK, 1.6))
        painter.drawRect(bounds)
        painter.setPen(QtGui.QPen(GOLD if primary else QtGui.QColor("#7f9aaa"), 0.8))
        painter.drawRect(bounds.adjusted(4, 4, -4, -4))

        painter.setPen(text)
        font = QtGui.QFont("Microsoft YaHei", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bounds, QtCore.Qt.AlignCenter, self.text())
        painter.end()


class RoundedVideoLabel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoCanvas")
        self.setMinimumSize(400, 230)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._frame_pixmap = QtGui.QPixmap()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 9)
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background: #10282b; color: #d9e3da; font-size: 13pt;"
        )
        self.image_label.setText("等待图像源")
        layout.addWidget(self.image_label)

    def setPixmap(self, pixmap):
        self._frame_pixmap = QtGui.QPixmap(pixmap)
        self.image_label.setText("")
        self._refresh_pixmap()

    def pixmap(self):
        return self._frame_pixmap

    def setText(self, text):
        self._frame_pixmap = QtGui.QPixmap()
        self.image_label.clear()
        self.image_label.setText(text)

    def _refresh_pixmap(self):
        if not self._frame_pixmap.isNull():
            scaled = self._frame_pixmap.scaled(
                self.image_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_pixmap()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        bounds = QtCore.QRectF(self.rect()).adjusted(2, 2, -2, -2)
        painter.fillRect(bounds, QtGui.QColor("#10282b"))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(INK, 3.0))
        painter.drawRect(bounds)
        painter.setPen(QtGui.QPen(QtGui.QColor("#89a8b7"), 1.0))
        painter.drawRect(bounds.adjusted(6, 6, -6, -6))
        painter.end()


def _card(name):
    card = OrnamentalPanel()
    card.setObjectName(name)
    return card


def _section_title(title, caption=None):
    group = QtWidgets.QVBoxLayout()
    group.setSpacing(0)
    heading = QtWidgets.QLabel(title)
    heading.setObjectName("panelTitle")
    heading.setFont(_title_font(15))
    heading.setMinimumHeight(28)
    group.addWidget(heading)
    if caption:
        note = QtWidgets.QLabel(caption)
        note.setObjectName("panelCaption")
        note.setMinimumHeight(18)
        group.addWidget(note)
    return group


def _metric_row(window, waste_type, accent):
    name = WASTE_NAMES[waste_type]
    row = QtWidgets.QFrame()
    row.setObjectName("metricRow")
    row.setMinimumHeight(42)
    layout = QtWidgets.QHBoxLayout(row)
    layout.setContentsMargins(12, 7, 12, 7)
    layout.setSpacing(10)

    dot = QtWidgets.QLabel()
    dot.setFixedSize(13, 13)
    dot.setStyleSheet(
        "background: {}; border: 1px solid #17365a; border-radius: 6px;".format(accent)
    )

    label = QtWidgets.QLabel(name)
    label.setObjectName("metricName")
    count = QtWidgets.QLabel("0")
    count.setObjectName("metricCount")
    count.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    count.setMinimumWidth(42)
    status = QtWidgets.QLabel("正常")
    status.setObjectName("metricState")
    status.setAlignment(QtCore.Qt.AlignCenter)
    status.setMinimumWidth(58)

    window.count_labels[name] = count
    window.bin_labels[name] = status
    layout.addWidget(dot)
    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(count)
    layout.addWidget(status)
    return row


def _status_pair(caption, value, object_name, width):
    group = QtWidgets.QVBoxLayout()
    group.setSpacing(1)
    label = QtWidgets.QLabel(caption)
    label.setObjectName("statusCaption")
    label.setAlignment(QtCore.Qt.AlignCenter)
    value.setObjectName(object_name)
    value.setMinimumWidth(width)
    value.setMinimumHeight(28)
    value.setAlignment(QtCore.Qt.AlignCenter)
    group.addWidget(label)
    group.addWidget(value)
    return group


def build_workspace(window):
    window.workspace_page.setObjectName("workspacePage")
    page_stack = QtWidgets.QStackedLayout(window.workspace_page)
    page_stack.setStackingMode(QtWidgets.QStackedLayout.StackAll)
    page_stack.addWidget(OrnamentalBackdrop())

    content = QtWidgets.QWidget()
    content.setObjectName("workspaceContent")
    page_stack.addWidget(content)
    page_stack.setCurrentWidget(content)

    root = QtWidgets.QVBoxLayout(content)
    root.setContentsMargins(58, 32, 58, 34)
    root.setSpacing(12)

    header = _card("headerCard")
    header_layout = QtWidgets.QHBoxLayout(header)
    header_layout.setContentsMargins(18, 12, 18, 12)
    header_layout.setSpacing(14)

    window.sky_button = window.sky_button_factory(window.audio)
    window.sky_button.setMinimumWidth(152)
    header_layout.addWidget(window.sky_button, 0, QtCore.Qt.AlignVCenter)
    header_layout.addStretch(1)

    title_group = QtWidgets.QVBoxLayout()
    title_group.setSpacing(0)
    title = QtWidgets.QLabel("智能垃圾视觉分拣系统")
    title.setObjectName("titleLabel")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setFont(_title_font(26))
    subtitle = QtWidgets.QLabel("实时识别  ·  稳定确认  ·  设备执行")
    subtitle.setObjectName("headerSubtitle")
    subtitle.setAlignment(QtCore.Qt.AlignCenter)
    title_group.addWidget(title)
    title_group.addWidget(subtitle)
    header_layout.addLayout(title_group, 3)
    header_layout.addStretch(1)

    right_header = QtWidgets.QVBoxLayout()
    right_header.setSpacing(4)
    audio_row = QtWidgets.QHBoxLayout()
    audio_row.setSpacing(12)
    window.workspace_click_toggle = window._make_audio_toggle(
        "按键声", window._click_sound_enabled, window._click_toggles
    )
    window.workspace_music_toggle = window._make_audio_toggle(
        "背景音乐",
        window._music_enabled,
        window._music_toggles,
        available=window.audio.music_available,
    )
    audio_row.addStretch(1)
    audio_row.addWidget(window.workspace_click_toggle)
    audio_row.addWidget(window.workspace_music_toggle)
    right_header.addLayout(audio_row)

    status_row = QtWidgets.QHBoxLayout()
    status_row.setSpacing(7)
    window.state_label = QtWidgets.QLabel("等待启动")
    window.connection_label = QtWidgets.QLabel("未连接")
    window.fps_label = QtWidgets.QLabel("0 FPS")
    status_row.addLayout(_status_pair("系统", window.state_label, "stateLabel", 112))
    status_row.addLayout(_status_pair("下位机", window.connection_label, "connectionLabel", 78))
    status_row.addLayout(_status_pair("实时帧率", window.fps_label, "fpsLabel", 66))
    right_header.addLayout(status_row)
    header_layout.addLayout(right_header, 0)
    root.addWidget(header)

    content_row = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
    content_row.setChildrenCollapsible(False)
    content_row.setHandleWidth(10)

    left = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(10)

    video_card = _card("panelCard")
    video_layout = QtWidgets.QVBoxLayout(video_card)
    video_layout.setContentsMargins(17, 13, 17, 15)
    video_layout.setSpacing(8)

    video_header = QtWidgets.QHBoxLayout()
    video_title = QtWidgets.QWidget()
    video_title_layout = QtWidgets.QVBoxLayout(video_title)
    video_title_layout.setContentsMargins(0, 0, 0, 0)
    video_title_layout.addLayout(_section_title("实时识别画面", "目标检测与分类可视化"))
    video_header.addWidget(video_title, 1)
    source_caption = QtWidgets.QLabel("输入")
    source_caption.setObjectName("statusCaption")
    window.source_label = QtWidgets.QLabel("正在连接图像源")
    window.source_label.setObjectName("sourceLabel")
    window.source_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    window.source_label.setMinimumWidth(230)
    window.source_label.setMaximumWidth(300)
    model_caption = QtWidgets.QLabel("模型")
    model_caption.setObjectName("statusCaption")
    window.model_label = QtWidgets.QLabel("等待加载")
    window.model_label.setObjectName("modelLabel")
    source_meta = QtWidgets.QVBoxLayout()
    source_meta.setSpacing(3)
    source_row = QtWidgets.QHBoxLayout()
    source_row.setSpacing(8)
    source_row.addWidget(source_caption)
    source_row.addWidget(window.source_label, 1)
    model_row = QtWidgets.QHBoxLayout()
    model_row.setSpacing(8)
    model_row.addWidget(model_caption)
    model_row.addWidget(window.model_label, 1)
    source_meta.addLayout(source_row)
    source_meta.addLayout(model_row)
    video_header.addLayout(source_meta, 0)
    video_layout.addLayout(video_header)

    window.camera_label = RoundedVideoLabel()
    window.camera_label.setText("等待图像源")
    video_layout.addWidget(window.camera_label, 1)

    progress_layout = QtWidgets.QHBoxLayout()
    progress_layout.setSpacing(10)
    window.time_label = QtWidgets.QLabel("00:00 / 00:00")
    window.time_label.setObjectName("timeLabel")
    window.time_label.setMinimumWidth(115)
    window.progress_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    window.progress_slider.setRange(0, 0)
    window.progress_slider.setEnabled(False)
    window.progress_slider.setToolTip("拖动跳转到视频位置")
    progress_layout.addWidget(window.time_label)
    progress_layout.addWidget(window.progress_slider, 1)
    video_layout.addLayout(progress_layout)
    left_layout.addWidget(video_card, 1)

    controls = _card("controlCard")
    controls_layout = QtWidgets.QHBoxLayout(controls)
    controls_layout.setContentsMargins(14, 10, 14, 10)
    controls_layout.setSpacing(9)
    window.video_button = WorkspaceButton("选择视频", window.audio)
    window.camera_button = WorkspaceButton("打开摄像头", window.audio)
    window.start_button = WorkspaceButton("开始识别", window.audio)
    window.start_button.setObjectName("primaryButton")
    window.reset_button = WorkspaceButton("清零计数", window.audio)
    window.quit_button = WorkspaceButton("退出", window.audio)
    window.quit_button.setObjectName("quitButton")
    controls_layout.addWidget(window.video_button)
    controls_layout.addWidget(window.camera_button)
    controls_layout.addStretch(1)
    controls_layout.addWidget(window.start_button)
    controls_layout.addWidget(window.reset_button)
    controls_layout.addWidget(window.quit_button)
    left_layout.addWidget(controls)
    content_row.addWidget(left)

    information = QtWidgets.QScrollArea()
    information.setObjectName("infoScroll")
    information.setWidgetResizable(True)
    information.setFrameShape(QtWidgets.QFrame.NoFrame)
    information.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    information.setMinimumWidth(385)
    information.setMaximumWidth(500)
    info_content = QtWidgets.QWidget()
    info_content.setObjectName("infoContent")
    info_layout = QtWidgets.QVBoxLayout(info_content)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setSpacing(10)

    result_card = _card("resultCard")
    result_card.setMinimumHeight(210)
    result_layout = QtWidgets.QVBoxLayout(result_card)
    result_layout.setContentsMargins(18, 12, 18, 13)
    result_layout.setSpacing(4)
    result_layout.addLayout(_section_title("当前识别结果", "YOLO 推理与置信度"))

    result_hero = QtWidgets.QHBoxLayout()
    result_text = QtWidgets.QVBoxLayout()
    category_caption = QtWidgets.QLabel("垃圾类别")
    category_caption.setObjectName("panelCaption")
    window.waste_label = QtWidgets.QLabel("—")
    window.waste_label.setObjectName("wasteLabel")
    result_text.addWidget(category_caption)
    result_text.addWidget(window.waste_label)
    result_hero.addLayout(result_text)
    result_hero.addStretch(1)
    confidence_group = QtWidgets.QVBoxLayout()
    confidence_caption = QtWidgets.QLabel("置信度")
    confidence_caption.setObjectName("panelCaption")
    window.confidence_label = QtWidgets.QLabel("—")
    window.confidence_label.setObjectName("confidenceBadge")
    window.confidence_label.setAlignment(QtCore.Qt.AlignCenter)
    window.confidence_label.setMinimumWidth(92)
    window.confidence_label.setMinimumHeight(34)
    confidence_group.addWidget(confidence_caption)
    confidence_group.addWidget(window.confidence_label)
    result_hero.addLayout(confidence_group)
    result_layout.addLayout(result_hero)

    class_row = QtWidgets.QHBoxLayout()
    class_caption = QtWidgets.QLabel("模型类别")
    class_caption.setObjectName("panelCaption")
    window.class_label = QtWidgets.QLabel("—")
    window.class_label.setObjectName("classLabel")
    class_row.addWidget(class_caption)
    class_row.addStretch(1)
    class_row.addWidget(window.class_label)
    result_layout.addLayout(class_row)
    info_layout.addWidget(result_card)

    stats_card = _card("panelCard")
    stats_card.setMinimumHeight(232)
    stats_layout = QtWidgets.QVBoxLayout(stats_card)
    stats_layout.setContentsMargins(16, 12, 16, 14)
    stats_layout.setSpacing(3)
    stats_layout.addLayout(_section_title("分拣统计"))
    accents = ("#4e78a8", "#6b8770", "#9d5454", "#787a80")
    for waste_type, accent in zip(
        (WasteType.RECYCLABLE, WasteType.KITCHEN, WasteType.HAZARDOUS, WasteType.OTHER),
        accents,
    ):
        stats_layout.addWidget(_metric_row(window, waste_type, accent))
    info_layout.addWidget(stats_card)

    communication_card = _card("logCard")
    communication_card.setMinimumHeight(215)
    communication_layout = QtWidgets.QVBoxLayout(communication_card)
    communication_layout.setContentsMargins(16, 12, 16, 14)
    communication_layout.setSpacing(7)
    log_header = QtWidgets.QHBoxLayout()
    log_header.addLayout(_section_title("通信日志"))
    log_header.addStretch(1)
    protocol = QtWidgets.QLabel("TX · RX")
    protocol.setObjectName("protocolBadge")
    log_header.addWidget(protocol)
    communication_layout.addLayout(log_header)
    window.log_browser = QtWidgets.QPlainTextEdit()
    window.log_browser.setReadOnly(True)
    window.log_browser.setMaximumBlockCount(500)
    communication_layout.addWidget(window.log_browser, 1)
    info_layout.addWidget(communication_card, 1)
    information.setWidget(info_content)
    content_row.addWidget(information)
    content_row.setStretchFactor(0, 7)
    content_row.setStretchFactor(1, 4)
    content_row.setSizes([900, 430])
    root.addWidget(content_row, 1)

    window.setStyleSheet(
        "QMainWindow { background: #dbe6e4; }"
        "QWidget#workspaceContent { color: #17365a; font-family: 'Microsoft YaHei';"
        " font-size: 10pt; background: transparent; }"
        "QLabel { background: transparent; }"
        "QLabel#titleLabel { color: #17365a; font-size: 25pt; font-weight: 700; }"
        "QLabel#headerSubtitle { color: #3d6683; font-size: 10pt; letter-spacing: 1px; }"
        "QLabel#panelTitle { color: #17365a; font-size: 15pt; font-weight: 700; }"
        "QLabel#panelCaption, QLabel#statusCaption { color: #52718a; font-size: 9pt; }"
        "QLabel#sourceLabel, QLabel#modelLabel { color: #17365a; background: #e6ece6;"
        " border: 1px solid #8ca4ae; border-radius: 2px; padding: 3px 7px; }"
        "QLabel#timeLabel { color: #355873; font-family: Consolas; font-size: 9pt; }"
        "QLabel#stateLabel, QLabel#connectionLabel, QLabel#fpsLabel {"
        " background: #245781; color: #f9f5e5; border: 1px solid #b79b5d;"
        " border-radius: 8px; padding: 3px 9px; font-weight: 600; }"
        "QLabel#connectionLabel { background: #2e746d; }"
        "QLabel#wasteLabel { color: #17365a; font-size: 25pt; font-weight: 700; }"
        "QLabel#confidenceBadge { color: #f8f4e5; background: #245781;"
        " border: 1px solid #b79b5d; border-radius: 10px; padding: 7px 10px;"
        " font-size: 13pt; font-weight: 700; }"
        "QLabel#classLabel { color: #385d78; font-family: Consolas; font-size: 11pt; }"
        "QFrame#metricRow { background: rgba(225, 233, 226, 170);"
        " border-bottom: 1px solid #b7c4c1; }"
        "QLabel#metricName { color: #254a68; font-size: 10pt; }"
        "QLabel#metricCount { color: #152f53; font-size: 16pt; font-weight: 700; }"
        "QLabel#metricState { color: #f7f3e5; background: #2d7580;"
        " border: 1px solid #b79b5d; border-radius: 7px; padding: 2px 7px;"
        " font-size: 9pt; font-weight: 700; }"
        "QLabel#protocolBadge { color: #315b7d; background: #e4ebe7;"
        " border: 1px solid #8ba1aa; border-radius: 8px; padding: 3px 9px; }"
        "QPlainTextEdit { background: #102f37; color: #dce8df; border: 2px solid #17365a;"
        " padding: 8px; selection-background-color: #4f7f86; font-family: Consolas;"
        " font-size: 9pt; }"
        "QScrollArea#infoScroll, QWidget#infoContent { background: transparent; border: 0; }"
        "QScrollBar:vertical { width: 9px; background: transparent; margin: 2px; }"
        "QScrollBar::handle:vertical { min-height: 34px; background: #6f8ea2;"
        " border-radius: 4px; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        "QSlider::groove:horizontal { height: 6px; background: #c4d1cf;"
        " border: 1px solid #9aadb0; border-radius: 3px; }"
        "QSlider::sub-page:horizontal { background: #477b9b; border-radius: 3px; }"
        "QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px;"
        " background: #d5bd80; border: 2px solid #426b86; }"
        "QSplitter::handle { background: transparent; }"
    )
