"""模拟器私有的阻塞式协议读写。

模拟器只需从 socket 精确读取一帧，因此这里故意不提供学员任务所需的
通用增量流解析器。上位机仍须自行处理噪声、半包和粘包。
"""

from dataclasses import dataclass
from enum import IntEnum
import socket


HEADER = b"\xAA\x55"


class Command(IntEnum):
    WASTE_RESULT = 0x01
    ACK = 0x02
    ACTION_DONE = 0x03
    BIN_FULL = 0x04
    START_COMPRESS = 0x05
    HEARTBEAT = 0x06
    ERROR = 0x7F


@dataclass(frozen=True)
class Packet:
    command: Command
    payload: bytes = b""

    def encode(self) -> bytes:
        body = bytes((int(self.command),)) + self.payload
        length = len(body)
        checksum = (length + sum(body)) & 0xFF
        return HEADER + bytes((length,)) + body + bytes((checksum,))


def _recv_exact(client: socket.socket, size: int) -> bytes:
    output = bytearray()
    while len(output) < size:
        part = client.recv(size - len(output))
        if not part:
            raise EOFError
        output.extend(part)
    return bytes(output)


def read_packet(client: socket.socket) -> Packet:
    """从模拟器连接中阻塞读取一帧；错误帧直接拒绝。"""
    header = _recv_exact(client, 2)
    if header != HEADER:
        raise ValueError("bad header")
    length = _recv_exact(client, 1)[0]
    if length < 1 or length > 64:
        raise ValueError("bad length")
    body = _recv_exact(client, length)
    checksum = _recv_exact(client, 1)[0]
    if checksum != ((length + sum(body)) & 0xFF):
        raise ValueError("bad checksum")
    return Packet(Command(body[0]), body[1:])
