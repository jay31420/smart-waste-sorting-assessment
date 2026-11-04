"""Deterministic lower-computer simulator used by Docker Compose."""

import argparse
import logging
import socket
import threading
import time
from typing import Tuple

from .protocol_reference import Command, Packet, read_packet


LOG = logging.getLogger("lower-simulator")


class LowerComputerSimulator:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, action_delay: float = 0.45) -> None:
        self.host = host
        self.port = port
        self.action_delay = action_delay
        self.sort_count = 0
        self._send_lock = threading.Lock()

    def serve_forever(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(4)
        LOG.info("模拟下位机监听 %s:%s", self.host, self.port)
        try:
            while True:
                client, address = server.accept()
                LOG.info("上位机已连接: %s:%s", *address)
                threading.Thread(target=self._handle_client, args=(client, address), daemon=True).start()
        finally:
            server.close()

    def _send_fragmented(self, client: socket.socket, packet: Packet) -> None:
        data = packet.encode()
        # Intentionally split packets to exercise a real stream parser.
        cut = min(3, len(data) - 1)
        with self._send_lock:
            client.sendall(data[:cut])
            time.sleep(0.015)
            client.sendall(data[cut:])
        LOG.info("TX %s", data.hex(" ").upper())

    def _handle_client(self, client: socket.socket, address: Tuple[str, int]) -> None:
        completed = set()
        try:
            while True:
                packet = read_packet(client)
                LOG.info("RX %s", packet.encode().hex(" ").upper())
                self._handle_packet(client, packet, completed)
        except (ConnectionError, EOFError, OSError, ValueError):
            pass
        finally:
            client.close()
            LOG.info("上位机断开: %s:%s", *address)

    def _handle_packet(self, client: socket.socket, packet: Packet, completed: set) -> None:
        if packet.command == Command.HEARTBEAT:
            self._send_fragmented(client, Packet(Command.ACK, bytes((Command.HEARTBEAT,))))
            return

        if packet.command not in (Command.WASTE_RESULT, Command.START_COMPRESS):
            self._send_fragmented(client, Packet(Command.ERROR, b"bad-command"))
            return

        sequence = packet.payload[0] if packet.payload else 0
        self._send_fragmented(client, Packet(Command.ACK, bytes((int(packet.command), sequence))))
        request_key = (int(packet.command), sequence)
        if request_key in completed:
            self._send_fragmented(client, Packet(Command.ACTION_DONE, bytes((sequence,))))
            return
        time.sleep(self.action_delay)
        completed.add(request_key)
        self._send_fragmented(client, Packet(Command.ACTION_DONE, bytes((sequence,))))

        if packet.command == Command.WASTE_RESULT:
            self.sort_count += 1
            # A repeatable full-bin event makes the UI state observable.
            if self.sort_count % 6 == 0 and len(packet.payload) >= 2:
                self._send_fragmented(client, Packet(Command.BIN_FULL, packet.payload[1:2]))


def main() -> None:
    parser = argparse.ArgumentParser(description="智能分拣下位机模拟器")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=9000, type=int)
    parser.add_argument("--delay", default=0.45, type=float)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [lower-sim] %(message)s")
    LowerComputerSimulator(args.host, args.port, args.delay).serve_forever()


if __name__ == "__main__":
    main()
