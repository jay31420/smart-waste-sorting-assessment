"""Painterly opening scene with a lightweight interactive workstation entry."""

from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets


class PaintedLandscape(QtWidgets.QWidget):
    computer_activated = QtCore.pyqtSignal()

    _SCENE_WIDTH = 1600.0
    _SCENE_HEIGHT = 900.0
    _COMPUTER_BOUNDS = QtCore.QRectF(70.0, 610.0, 500.0, 258.0)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._hover_progress = 0.0
        background_path = Path(__file__).resolve().parent.parent / "assets" / "scene_oil_landscape.png"
        self._background = QtGui.QPixmap(str(background_path))
        self._scaled_background = QtGui.QPixmap()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(110)
        self._timer.timeout.connect(self._advance_scene)
        self._hover_animation = QtCore.QVariantAnimation(self)
        self._hover_animation.setDuration(180)
        self._hover_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._hover_animation.valueChanged.connect(self._set_hover_progress)
        self.setMinimumSize(760, 430)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event):
        scale = max(self.width() / self._SCENE_WIDTH, self.height() / self._SCENE_HEIGHT)
        target_width = max(1, int(self._SCENE_WIDTH * scale) + 24)
        target_height = max(1, int(self._SCENE_HEIGHT * scale) + 24)
        if not self._background.isNull():
            self._scaled_background = self._background.scaled(
                target_width,
                target_height,
                QtCore.Qt.KeepAspectRatioByExpanding,
                QtCore.Qt.SmoothTransformation,
            )
        super().resizeEvent(event)

    def _advance_scene(self):
        self._phase = (self._phase + 0.0015) % 1.0
        self.update()

    def _set_hover_progress(self, value):
        self._hover_progress = float(value)
        self.update()

    def _start_hover_animation(self, target):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._hover_progress)
        self._hover_animation.setEndValue(float(target))
        self._hover_animation.start()

    def _scene_transform(self, painter):
        scale = min(self.width() / self._SCENE_WIDTH, self.height() / self._SCENE_HEIGHT)
        x_offset = (self.width() - self._SCENE_WIDTH * scale) / 2.0
        y_offset = (self.height() - self._SCENE_HEIGHT * scale) / 2.0
        painter.translate(x_offset, y_offset)
        painter.scale(scale, scale)
        return scale, x_offset, y_offset

    @staticmethod
    def _draw_halo_text(painter, rect, text, font, color):
        painter.setFont(font)
        painter.setPen(QtGui.QColor(248, 246, 232, 165))
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (1, 1)):
            painter.drawText(rect.translated(dx, dy), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)
        painter.setPen(color)
        painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)

    def _draw_background(self, painter):
        if self._scaled_background.isNull():
            gradient = QtGui.QLinearGradient(0, 0, 0, self._SCENE_HEIGHT)
            gradient.setColorAt(0.0, QtGui.QColor("#b7d5d4"))
            gradient.setColorAt(0.55, QtGui.QColor("#d8d7aa"))
            gradient.setColorAt(1.0, QtGui.QColor("#8a956d"))
            painter.fillRect(QtCore.QRectF(0, 0, self._SCENE_WIDTH, self._SCENE_HEIGHT), gradient)
            return

        dx = -12.0 + self._phase * 24.0
        dy = -12.0 + self._phase * 5.0
        painter.drawPixmap(
            QtCore.QRect(
                int(dx),
                int(dy),
                int(self._SCENE_WIDTH + 24),
                int(self._SCENE_HEIGHT + 24),
            ),
            self._scaled_background,
        )

        haze = QtGui.QLinearGradient(0, 0, 0, self._SCENE_HEIGHT)
        haze.setColorAt(0.0, QtGui.QColor(247, 246, 230, 18))
        haze.setColorAt(0.48, QtGui.QColor(247, 246, 230, 0))
        haze.setColorAt(1.0, QtGui.QColor(29, 62, 55, 28))
        painter.fillRect(QtCore.QRectF(0, 0, self._SCENE_WIDTH, self._SCENE_HEIGHT), haze)

    def _draw_headline(self, painter):
        self._draw_halo_text(
            painter,
            QtCore.QRectF(102, 62, 830, 54),
            "让垃圾回到正确的地方",
            QtGui.QFont("Microsoft YaHei", 24, QtGui.QFont.Bold),
            QtGui.QColor("#204947"),
        )
        painter.setFont(QtGui.QFont("Microsoft YaHei", 11))
        painter.setPen(QtGui.QColor("#365e59"))
        painter.drawText(
            QtCore.QRectF(106, 121, 900, 30),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            "视觉识别  ·  稳定确认  ·  把自然与城市生活连在一起",
        )

        painter.setPen(QtGui.QPen(QtGui.QColor(239, 238, 221, 160), 1.2))
        painter.setBrush(QtGui.QColor(28, 56, 53, 178))
        painter.drawRoundedRect(QtCore.QRectF(1072, 82, 426, 54), 27, 27)
        painter.setPen(QtGui.QColor("#fbf6e5"))
        painter.setFont(QtGui.QFont("Microsoft YaHei", 10, QtGui.QFont.Medium))
        painter.drawText(
            QtCore.QRectF(1088, 82, 394, 54),
            QtCore.Qt.AlignCenter,
            "点击电脑进入工作台",
        )

    def _draw_computer_entry(self, painter):
        grow = int(round(self._hover_progress * 4))
        card = self._COMPUTER_BOUNDS.adjusted(-grow, -grow, grow, grow)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(32, 47, 41, 54))
        painter.drawEllipse(
            QtCore.QRectF(card.left() + 24, card.bottom() - 16, card.width() - 48, 40)
        )

        border = QtGui.QColor(231, 225, 198, 140 + int(75 * self._hover_progress))
        fill = QtGui.QColor(241, 240, 224, 214 + int(24 * self._hover_progress))
        painter.setPen(QtGui.QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(card, 22.0, 22.0)

        icon = QtCore.QRectF(card.left() + 24, card.top() + 30, 206, 172)
        painter.setPen(QtGui.QPen(QtGui.QColor("#536763"), 3.0))
        painter.setBrush(QtGui.QColor(29, 56, 58, 246))
        painter.drawRoundedRect(icon, 13.0, 13.0)

        screen = QtCore.QRectF(icon.left() + 13, icon.top() + 13, icon.width() - 26, icon.height() - 47)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#e7eee2"))
        painter.drawRoundedRect(screen, 7.0, 7.0)

        top = int(screen.top())
        left = int(screen.left())
        painter.setBrush(QtGui.QColor("#2a6f70"))
        painter.drawRoundedRect(QtCore.QRect(left + 14, top + 15, int(screen.width()) - 28, 19), 5, 5)
        painter.setBrush(QtGui.QColor("#5f7e68"))
        painter.drawEllipse(QtCore.QRect(left + 22, top + 53, 44, 44))
        painter.setBrush(QtGui.QColor("#c39a58"))
        painter.drawEllipse(QtCore.QRect(left + 82, top + 53, 44, 44))
        painter.setBrush(QtGui.QColor("#63879a"))
        painter.drawEllipse(QtCore.QRect(left + 142, top + 53, 28, 28))

        painter.setPen(QtGui.QPen(QtGui.QColor("#78918a"), 4, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        bottom = int(screen.bottom()) - 25
        painter.drawLine(left + 24, bottom, int(screen.right()) - 30, bottom)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#c9c9b7"))
        painter.drawRoundedRect(QtCore.QRect(left + 18, int(icon.bottom()) - 15, int(icon.width()) - 36, 8), 4, 4)

        text_left = int(card.left() + 254)
        text_top = int(card.top())
        text_width = int(card.width()) - 286
        painter.setPen(QtGui.QColor("#1f4847"))
        painter.setFont(QtGui.QFont("Microsoft YaHei", 14, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRect(text_left, text_top + 60, text_width, 42), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, "智能工作台")
        painter.setPen(QtGui.QColor("#5a7068"))
        painter.setFont(QtGui.QFont("Microsoft YaHei", 9))
        painter.drawText(
            QtCore.QRect(text_left, text_top + 103, text_width, 30),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            "点击进入分拣控制",
        )

        arrow_x = int(card.right()) - 46
        arrow_y = int(card.center().y()) + 34
        painter.setPen(QtGui.QPen(QtGui.QColor("#2f7772"), 2.2))
        painter.drawLine(arrow_x - 12, arrow_y, arrow_x + 10, arrow_y)
        painter.drawLine(arrow_x + 3, arrow_y - 7, arrow_x + 10, arrow_y)
        painter.drawLine(arrow_x + 3, arrow_y + 7, arrow_x + 10, arrow_y)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor("#d9dfcb"))
        self._scene_transform(painter)

        painter.save()
        painter.setClipRect(QtCore.QRectF(0, 0, self._SCENE_WIDTH, self._SCENE_HEIGHT))
        self._draw_background(painter)
        self._draw_headline(painter)
        self._draw_computer_entry(painter)
        painter.restore()
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.handle_scene_click(event.pos()):
            event.accept()
            return
        super().mousePressEvent(event)

    def handle_scene_click(self, widget_point):
        _, x_offset, y_offset = self._scene_transform_values()
        scale = min(self.width() / self._SCENE_WIDTH, self.height() / self._SCENE_HEIGHT)
        point = QtCore.QPointF((widget_point.x() - x_offset) / scale, (widget_point.y() - y_offset) / scale)
        if self._COMPUTER_BOUNDS.contains(point):
            self.computer_activated.emit()
            return True
        return False

    def _scene_transform_values(self):
        scale = min(self.width() / self._SCENE_WIDTH, self.height() / self._SCENE_HEIGHT)
        x_offset = (self.width() - self._SCENE_WIDTH * scale) / 2.0
        y_offset = (self.height() - self._SCENE_HEIGHT * scale) / 2.0
        return scale, x_offset, y_offset

    def mouseMoveEvent(self, event):
        _, x_offset, y_offset = self._scene_transform_values()
        scale = min(self.width() / self._SCENE_WIDTH, self.height() / self._SCENE_HEIGHT)
        point = QtCore.QPointF((event.x() - x_offset) / scale, (event.y() - y_offset) / scale)
        self.setCursor(QtCore.Qt.PointingHandCursor if self._COMPUTER_BOUNDS.contains(point) else QtCore.Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        self._start_hover_animation(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._start_hover_animation(0.0)
        super().leaveEvent(event)


class SceneOverlay(QtWidgets.QWidget):
    """Forward opening-scene clicks while keeping audio controls interactive."""

    def __init__(self, landscape, parent=None):
        super().__init__(parent)
        self.landscape = landscape
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.landscape.handle_scene_click(event.pos()):
            event.accept()
            return
        event.ignore()

    def mouseMoveEvent(self, event):
        _, x_offset, y_offset = self.landscape._scene_transform_values()
        scale = min(
            self.landscape.width() / self.landscape._SCENE_WIDTH,
            self.landscape.height() / self.landscape._SCENE_HEIGHT,
        )
        scene_point = QtCore.QPointF(
            (event.pos().x() - x_offset) / scale,
            (event.pos().y() - y_offset) / scale,
        )
        self.setCursor(
            QtCore.Qt.PointingHandCursor
            if self.landscape._COMPUTER_BOUNDS.contains(scene_point)
            else QtCore.Qt.ArrowCursor
        )
