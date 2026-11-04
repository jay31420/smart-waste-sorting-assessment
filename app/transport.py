"""Replaceable byte transports for Docker/TCP, tests and the real Nano serial port."""

import queue
import socket
import threading
from abc import ABC, abstractmethod
from typing import List, Optional

from .protocol import Packet, StreamParser


class TransportError(RuntimeError):
    pass


class Transport(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def send(self, packet: Packet) -> None:
        raise NotImplementedError

    @abstractmethod
    def poll(self) -> List[Packet]:
        raise NotImplementedError

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError


class TcpTransport(Transport):
    """TCP is used in Docker while preserving the exact binary protocol."""

    def __init__(self, host: str, port: int, timeout: float = 2.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = None  # type: Optional[socket.socket]
        self._connected = False
        self._packets = queue.Queue()  # type: queue.Queue
        self._stop = threading.Event()
        self._reader = None  # type: Optional[threading.Thread]
        self._send_lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        if self._connected:
            return
        if self._socket is not None:
            self.close()
        sock = socket.create_connection((self.host, self.port), self.timeout)
        sock.settimeout(0.5)
        self._socket = sock
        self._connected = True
        self._stop.clear()
        self._reader = threading.Thread(target=self._read_loop, args=(sock,), name="protocol-reader", daemon=True)
        self._reader.start()

    def _read_loop(self, sock: socket.socket) -> None:
        parser = StreamParser()
        try:
            while not self._stop.is_set():
                try:
                    chunk = sock.recv(1024)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                for packet in parser.feed(chunk):
                    self._packets.put(packet)
        except OSError:
            pass
        finally:
            self._connected = False

    def send(self, packet: Packet) -> None:
        if not self._connected or self._socket is None:
            raise TransportError("下位机未连接")
        try:
            with self._send_lock:
                self._socket.sendall(packet.encode())
        except OSError as exc:
            self._connected = False
            raise TransportError(str(exc))

    def poll(self) -> List[Packet]:
        packets = []
        while True:
            try:
                packets.append(self._packets.get_nowait())
            except queue.Empty:
                return packets

    def close(self) -> None:
        self._stop.set()
        sock, self._socket = self._socket, None
        self._connected = False
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        if self._reader is not None and self._reader.is_alive():
            self._reader.join(timeout=1.0)


class SerialTransport(Transport):
    """Real hardware adapter. Importing pyserial is intentionally lazy."""

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 0.05) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None
        self._parser = StreamParser()

    @property
    def connected(self) -> bool:
        return bool(self._serial is not None and self._serial.is_open)

    def connect(self) -> None:
        try:
            import serial
        except ImportError as exc:
            raise TransportError("缺少 pyserial，无法使用真实串口") from exc
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def send(self, packet: Packet) -> None:
        if not self.connected:
            raise TransportError("串口未连接")
        self._serial.write(packet.encode())

    def poll(self) -> List[Packet]:
        if not self.connected:
            return []
        waiting = self._serial.in_waiting
        data = self._serial.read(waiting or 1)
        return self._parser.feed(data)

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None


class MemoryTransport(Transport):
    """Deterministic transport used by public and hidden tests."""

    def __init__(self) -> None:
        self.sent = []  # type: List[Packet]
        self.incoming = []  # type: List[Packet]
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def send(self, packet: Packet) -> None:
        if not self.connected:
            raise TransportError("memory transport is not connected")
        self.sent.append(packet)

    def feed(self, *packets: Packet) -> None:
        self.incoming.extend(packets)

    def poll(self) -> List[Packet]:
        packets, self.incoming = self.incoming, []
        return packets
