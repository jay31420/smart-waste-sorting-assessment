"""与 UI 无关的分拣控制状态机。"""

import time
from enum import Enum
from typing import Callable, Dict, Optional

from .detectors import Detection
from .protocol import Command, Packet, WasteType, WASTE_NAMES
from .transport import Transport, TransportError


class SystemState(Enum):
    IDLE = "等待识别"
    WAIT_ACK = "等待下位机确认"
    EXECUTING = "下位机执行中"
    COOLDOWN = "等待物体离开"
    COMPRESSING = "压缩中"
    PAUSED = "已暂停"
    ERROR = "通信异常"


EventCallback = Callable[[str, dict], None]


class SortingController:
    def __init__(
        self,
        transport: Transport,
        event_callback: Optional[EventCallback] = None,
        stable_frames: int = 3,
        ack_timeout: float = 2.0,
        max_retries: int = 2,
        compress_after: int = 20,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if stable_frames < 1:
            raise ValueError("稳定识别帧数必须大于 0")
        if ack_timeout <= 0:
            raise ValueError("确认超时时间必须大于 0")
        if max_retries < 0:
            raise ValueError("最大重试次数不能小于 0")
        self.transport = transport
        self.event_callback = event_callback or (lambda _name, _data: None)
        self.stable_frames = stable_frames
        self.ack_timeout = ack_timeout
        self.max_retries = max_retries
        self.compress_after = compress_after
        self.clock = clock
        self.counts = {item: 0 for item in WasteType}
        self.bin_full = {item: False for item in WasteType}
        self.state = SystemState.IDLE
        self.pending = None  # type: Optional[WasteType]
        self._candidate = None  # type: Optional[WasteType]
        self._stable_count = 0
        self._missing_frames = 0
        self._last_packet = None  # type: Optional[Packet]
        self._deadline = 0.0
        self._retry_count = 0
        self._compress_sent = False
        self._sequence = 0
        self._active_sequence = None  # type: Optional[int]

    def _emit(self, name: str, **data) -> None:
        self.event_callback(name, data)

    def _set_state(self, state: SystemState) -> None:
        if state != self.state:
            self.state = state
            self._emit("state", value=state.value)

    def reset(self) -> None:
        self.counts = {item: 0 for item in WasteType}
        self.bin_full = {item: False for item in WasteType}
        self._candidate = None
        self._stable_count = 0
        self._compress_sent = False
        self._emit("counts", values=self.named_counts())
        self._emit("bins", values=self.named_bins())

    def named_counts(self) -> Dict[str, int]:
        return {WASTE_NAMES[key]: value for key, value in self.counts.items()}

    def named_bins(self) -> Dict[str, bool]:
        return {WASTE_NAMES[key]: value for key, value in self.bin_full.items()}

    def process_detection(self, detection: Optional[Detection]) -> None:
        """连续稳定识别后触发一次；物体离开若干帧后才重新布防。"""
        if self.state == SystemState.COOLDOWN:
            if detection is None:
                self._missing_frames += 1
                if self._missing_frames >= self.stable_frames:
                    self._missing_frames = 0
                    self._candidate = None
                    self._stable_count = 0
                    self._set_state(SystemState.IDLE)
            else:
                self._missing_frames = 0
            return

        if self.state != SystemState.IDLE:
            return

        if detection is None:
            self._candidate = None
            self._stable_count = 0
            return

        if detection.waste_type == self._candidate:
            self._stable_count += 1
        else:
            self._candidate = detection.waste_type
            self._stable_count = 1

        if self._stable_count >= self.stable_frames:
            self._send_classification(detection.waste_type)

    def _send_packet(self, packet: Packet, wait_for_reply: bool = True) -> None:
        try:
            self.transport.send(packet)
        except TransportError as exc:
            self._last_packet = None
            self.pending = None
            self._active_sequence = None
            self._set_state(SystemState.ERROR)
            self._emit("log", message="发送失败：{}".format(exc))
            return
        self._emit("tx", packet=packet.encode().hex(" ").upper())
        if wait_for_reply:
            self._last_packet = packet
            self._deadline = self.clock() + self.ack_timeout
            self._retry_count = 0

    def _send_classification(self, waste_type: WasteType) -> None:
        if self.bin_full[waste_type]:
            self._missing_frames = 0
            self._set_state(SystemState.COOLDOWN)
            self._emit("log", message="{}已满载，暂不发送分拣指令".format(WASTE_NAMES[waste_type]))
            return

        self._sequence = (self._sequence + 1) & 0xFF
        self._active_sequence = self._sequence
        self.pending = waste_type
        packet = Packet(
            Command.WASTE_RESULT,
            bytes((self._active_sequence, int(waste_type))),
        )
        self._set_state(SystemState.WAIT_ACK)
        self._send_packet(packet)

    def poll(self) -> None:
        for packet in self.transport.poll():
            self._emit("rx", packet=packet.encode().hex(" ").upper())
            self.handle_packet(packet)

        if self._last_packet is None or self.state not in (
            SystemState.WAIT_ACK,
            SystemState.EXECUTING,
            SystemState.COMPRESSING,
        ):
            return
        if self.clock() < self._deadline:
            return

        if self._retry_count >= self.max_retries:
            self._last_packet = None
            self.pending = None
            self._active_sequence = None
            self._set_state(SystemState.ERROR)
            self._emit("log", message="等待下位机响应超时，已停止重试")
            return

        try:
            self.transport.send(self._last_packet)
        except TransportError as exc:
            self._last_packet = None
            self.pending = None
            self._active_sequence = None
            self._set_state(SystemState.ERROR)
            self._emit("log", message="重发失败：{}".format(exc))
            return
        self._emit("tx", packet=self._last_packet.encode().hex(" ").upper())
        self._retry_count += 1
        self._deadline = self.clock() + self.ack_timeout

    def handle_packet(self, packet: Packet) -> None:
        if packet.command == Command.ACK:
            if len(packet.payload) < 2 or self._last_packet is None:
                return
            original_command, sequence = packet.payload[:2]
            if sequence != self._active_sequence or original_command != int(self._last_packet.command):
                return
            if self.state == SystemState.WAIT_ACK:
                if self._last_packet.command == Command.WASTE_RESULT:
                    self._set_state(SystemState.EXECUTING)
                elif self._last_packet.command == Command.START_COMPRESS:
                    self._set_state(SystemState.COMPRESSING)
                self._deadline = self.clock() + self.ack_timeout
            return

        if packet.command == Command.ACTION_DONE:
            if len(packet.payload) < 1 or self._last_packet is None:
                return
            sequence = packet.payload[0]
            if sequence != self._active_sequence:
                return

            completed_command = self._last_packet.command
            self._last_packet = None
            self._active_sequence = None
            self._retry_count = 0
            if completed_command == Command.WASTE_RESULT and self.pending is not None:
                self.counts[self.pending] += 1
                self._emit("counts", values=self.named_counts())
                self.pending = None
                self._missing_frames = 0
                self._set_state(SystemState.COOLDOWN)
                self._maybe_compress()
            elif completed_command == Command.START_COMPRESS:
                self._set_state(SystemState.COOLDOWN)
            return

        if packet.command == Command.BIN_FULL:
            if not packet.payload:
                return
            try:
                waste_type = WasteType(packet.payload[0])
            except ValueError:
                return
            self.bin_full[waste_type] = True
            self._emit("bins", values=self.named_bins())
            return

        if packet.command == Command.ERROR:
            message = packet.payload.decode("utf-8", errors="replace")
            self._last_packet = None
            self.pending = None
            self._active_sequence = None
            self._set_state(SystemState.ERROR)
            self._emit("log", message="下位机错误：{}".format(message))

    def _maybe_compress(self) -> None:
        if self._compress_sent or self.compress_after <= 0:
            return
        if sum(self.counts.values()) < self.compress_after:
            return

        self._compress_sent = True
        self._sequence = (self._sequence + 1) & 0xFF
        self._active_sequence = self._sequence
        self._set_state(SystemState.COMPRESSING)
        self._send_packet(Packet(Command.START_COMPRESS, bytes((self._active_sequence,))))
