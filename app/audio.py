"""Optional local audio feedback for the desktop interface."""

import json
import os
from pathlib import Path

from PyQt5 import QtCore

try:
    from PyQt5.QtMultimedia import (
        QAudioDeviceInfo,
        QMediaContent,
        QMediaPlayer,
        QSoundEffect,
    )
except ImportError:
    QAudioDeviceInfo = None
    QMediaContent = None
    QMediaPlayer = None
    QSoundEffect = None


class AudioFeedback(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available = False
        self.web_music_state_path = (
            Path(os.environ["WEB_MUSIC_STATE_FILE"])
            if os.environ.get("WEB_MUSIC_STATE_FILE")
            else None
        )
        self.music_available = self.web_music_state_path is not None
        self.click_enabled = True
        self.music_enabled = False
        self._music = None
        self._click = None

        if (
            QSoundEffect is None
            or QMediaPlayer is None
            or QAudioDeviceInfo is None
            or QAudioDeviceInfo.defaultOutputDevice().isNull()
        ):
            return

        assets = Path(__file__).resolve().parent.parent / "assets"
        music_path = assets / "cycling_music.mp3"
        click_path = assets / "button_tap.wav"
        if not music_path.is_file() or not click_path.is_file():
            return

        self._music = QMediaPlayer(self)
        self._music.setMedia(
            QMediaContent(QtCore.QUrl.fromLocalFile(str(music_path)))
        )
        self._music.setVolume(12)
        self._music.mediaStatusChanged.connect(self._on_music_status_changed)
        self._click = QSoundEffect(self)
        self._click.setSource(QtCore.QUrl.fromLocalFile(str(click_path)))
        self._click.setLoopCount(1)
        self._click.setVolume(0.24)
        self.available = True
        self.music_available = True

    def play_click(self):
        if self.available and self.click_enabled:
            self._click.play()

    def set_click_enabled(self, enabled):
        self.click_enabled = bool(enabled)

    def set_music_enabled(self, enabled):
        self.music_enabled = bool(enabled)
        self._write_web_music_state()
        if not self.available:
            return
        if self.music_enabled:
            if self._music.state() != QMediaPlayer.PlayingState:
                self._music.play()
        else:
            self._music.stop()

    def set_volume(self, value):
        if self.available:
            self._music.setVolume(
                int(max(0.0, min(1.0, float(value))) * 100)
            )

    def _on_music_status_changed(self, status):
        if (
            self.music_enabled
            and status == QMediaPlayer.EndOfMedia
            and self._music is not None
        ):
            self._music.setPosition(0)
            self._music.play()

    def _write_web_music_state(self):
        if self.web_music_state_path is None:
            return
        payload = json.dumps(
            {"enabled": self.music_enabled},
            ensure_ascii=False,
        )
        temporary = self.web_music_state_path.with_suffix(".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.web_music_state_path)

    def stop(self):
        if self.available:
            self._music.stop()
            self._click.stop()
