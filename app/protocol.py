"""上位机通信协议。

帧格式请阅读仓库根目录的 ``PROTOCOL.md``。TCP/串口读取可能返回任意长度的
字节片段，因此解析器会缓存数据并增量提取完整帧。
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import List


HEADER = b"\xAA\x55"
MAX_BODY_LENGTH = 64


class Command(IntEnum):
    WASTE_RESULT = 0x01
    ACK = 0x02
    ACTION_DONE = 0x03
    BIN_FULL = 0x04
    START_COMPRESS = 0x05
    HEARTBEAT = 0x06
    ERROR = 0x7F


class WasteType(IntEnum):
    HAZARDOUS = 0x01
    OTHER = 0x02
    RECYCLABLE = 0x03
    KITCHEN = 0x04


WASTE_NAMES = {
    WasteType.RECYCLABLE: "可回收垃圾",
    WasteType.KITCHEN: "厨余垃圾",
    WasteType.HAZARDOUS: "有害垃圾",
    WasteType.OTHER: "其他垃圾",
}


@dataclass(frozen=True)
class Packet:
    command: Command
    payload: bytes = b""

    def encode(self) -> bytes:
        """生成 ``HEADER + LENGTH + COMMAND + PAYLOAD + CHECKSUM``。"""
        command = int(self.command)
        if not 0 <= command <= 0xFF:
            raise ValueError("命令字必须是一个字节")
        if not isinstance(self.payload, (bytes, bytearray, memoryview)):
            raise TypeError("载荷必须是 bytes-like 对象")

        payload = bytes(self.payload)
        length = 1 + len(payload)
        if not 1 <= length <= MAX_BODY_LENGTH:
            raise ValueError("帧体长度必须在 1～{} 字节之间".format(MAX_BODY_LENGTH))

        body = bytes((command,)) + payload
        checksum = (length + sum(body)) & 0xFF
        return HEADER + bytes((length,)) + body + bytes((checksum,))


class StreamParser:
    """把任意分片的 TCP/串口字节流增量解析为 Packet。"""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.error_count = 0

    def reset(self) -> None:
        self._buffer.clear()
        self.error_count = 0

    def feed(self, data: bytes) -> List[Packet]:
        """增量解析字节流；未收完整的帧留到下一次调用。"""
        self._buffer.extend(data)
        packets = []  # type: List[Packet]

        while True:
            header_index = self._buffer.find(HEADER)
            if header_index < 0:
                # 保留可能是下一段帧头开头的 AA 字节。
                keep_tail = self._buffer[-1:] == HEADER[:1]
                self._buffer.clear()
                if keep_tail:
                    self._buffer.extend(HEADER[:1])
                break
            if header_index:
                del self._buffer[:header_index]

            if len(self._buffer) < 3:
                break

            length = self._buffer[2]
            if not 1 <= length <= MAX_BODY_LENGTH:
                self.error_count += 1
                del self._buffer[0]
                continue

            frame_size = length + 4
            if len(self._buffer) < frame_size:
                break

            expected_checksum = sum(self._buffer[2 : frame_size - 1]) & 0xFF
            if self._buffer[frame_size - 1] != expected_checksum:
                self.error_count += 1
                # Drop one byte so a later header, including one already buffered,
                # can be found without assuming the corrupted frame length is sound.
                del self._buffer[0]
                continue

            try:
                command = Command(self._buffer[3])
            except ValueError:
                self.error_count += 1
                del self._buffer[:frame_size]
                continue

            payload = bytes(self._buffer[4 : frame_size - 1])
            packets.append(Packet(command, payload))
            del self._buffer[:frame_size]

        return packets
