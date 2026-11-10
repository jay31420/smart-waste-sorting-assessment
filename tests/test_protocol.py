import unittest

from app.protocol import Command, Packet, StreamParser


class ProtocolTests(unittest.TestCase):
    def test_packet_encoding_matches_protocol_example(self):
        packet = Packet(Command.WASTE_RESULT, b"\x11\x03")
        self.assertEqual(packet.encode(), bytes.fromhex("AA 55 03 01 11 03 18"))

    def test_packet_can_arrive_one_byte_at_a_time(self):
        packet = Packet(Command.WASTE_RESULT, b"\x11\x03")
        parser = StreamParser()
        output = []
        for byte in packet.encode():
            output.extend(parser.feed(bytes((byte,))))
        self.assertEqual(output, [packet])

    def test_noise_bad_checksum_and_sticky_packets_are_recovered(self):
        first = Packet(Command.ACK, b"\x01\x11")
        second = Packet(Command.ACTION_DONE, b"\x11")
        damaged = bytearray(first.encode())
        damaged[-1] ^= 0xFF
        parser = StreamParser()
        output = parser.feed(b"noise" + bytes(damaged) + first.encode() + second.encode())
        self.assertEqual(output, [first, second])
        self.assertGreaterEqual(parser.error_count, 1)

    def test_packet_rejects_payload_that_exceeds_protocol_limit(self):
        with self.assertRaises(ValueError):
            Packet(Command.ERROR, b"x" * 64).encode()

    def test_parser_recovers_after_invalid_length(self):
        packet = Packet(Command.HEARTBEAT)
        parser = StreamParser()
        output = parser.feed(b"\xAA\x55\x00" + packet.encode())
        self.assertEqual(output, [packet])
        self.assertEqual(parser.error_count, 1)


if __name__ == "__main__":
    unittest.main()
