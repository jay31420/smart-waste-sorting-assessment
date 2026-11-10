import unittest

from app.controller import SortingController, SystemState
from app.detectors import Detection
from app.protocol import Command, Packet, WasteType
from app.transport import MemoryTransport


class FakeClock:
    def __init__(self):
        self.value = 10.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.transport = MemoryTransport()
        self.transport.connect()
        self.clock = FakeClock()
        self.events = []
        self.controller = SortingController(
            self.transport,
            lambda name, data: self.events.append((name, data)),
            clock=self.clock,
        )
        self.detection = Detection(WasteType.RECYCLABLE, "blue-token", 0.9, (1, 2, 3, 4))

    def test_stable_detection_drives_one_complete_sort_cycle(self):
        for _ in range(3):
            self.controller.process_detection(self.detection)
        self.assertEqual(self.controller.state, SystemState.WAIT_ACK)
        self.assertEqual(len(self.transport.sent), 1)
        sent = self.transport.sent[0]
        self.assertEqual(sent.command, Command.WASTE_RESULT)
        self.assertEqual(sent.payload[1], WasteType.RECYCLABLE)
        sequence = sent.payload[0]

        self.transport.feed(Packet(Command.ACK, bytes((Command.WASTE_RESULT, sequence))))
        self.controller.poll()
        self.assertEqual(self.controller.state, SystemState.EXECUTING)

        self.transport.feed(Packet(Command.ACTION_DONE, bytes((sequence,))))
        self.controller.poll()
        self.assertEqual(self.controller.counts[WasteType.RECYCLABLE], 1)
        self.assertEqual(self.controller.state, SystemState.COOLDOWN)

    def test_timeout_retries_then_enters_error(self):
        for _ in range(3):
            self.controller.process_detection(self.detection)
        for _ in range(3):
            self.clock.advance(2.1)
            self.controller.poll()
        self.assertEqual(self.controller.state, SystemState.ERROR)
        self.assertEqual(len(self.transport.sent), 3)

    def test_full_bin_prevents_sending_that_category(self):
        self.controller.handle_packet(Packet(Command.BIN_FULL, bytes((WasteType.RECYCLABLE,))))
        for _ in range(3):
            self.controller.process_detection(self.detection)
        self.assertEqual(self.transport.sent, [])
        self.assertEqual(self.controller.state, SystemState.COOLDOWN)

    def test_completed_object_is_not_sent_again_until_it_leaves(self):
        for _ in range(3):
            self.controller.process_detection(self.detection)
        sequence = self.transport.sent[0].payload[0]
        self.transport.feed(Packet(Command.ACTION_DONE, bytes((sequence,))))
        self.controller.poll()

        for _ in range(10):
            self.controller.process_detection(self.detection)
        self.assertEqual(len(self.transport.sent), 1)

        for _ in range(3):
            self.controller.process_detection(None)
        for _ in range(3):
            self.controller.process_detection(self.detection)
        self.assertEqual(len(self.transport.sent), 2)

    def test_action_done_for_another_sequence_does_not_count(self):
        for _ in range(3):
            self.controller.process_detection(self.detection)
        self.controller.handle_packet(Packet(Command.ACTION_DONE, b"\xFF"))
        self.assertEqual(self.controller.counts[WasteType.RECYCLABLE], 0)

    def test_reset_does_not_discard_an_in_flight_sort(self):
        for _ in range(3):
            self.controller.process_detection(self.detection)
        sequence = self.transport.sent[0].payload[0]
        self.controller.reset()
        self.transport.feed(Packet(Command.ACTION_DONE, bytes((sequence,))))
        self.controller.poll()
        self.assertEqual(self.controller.counts[WasteType.RECYCLABLE], 1)

    def test_compression_starts_once_after_count_threshold(self):
        self.controller.compress_after = 1
        for _ in range(3):
            self.controller.process_detection(self.detection)
        sequence = self.transport.sent[0].payload[0]
        self.transport.feed(Packet(Command.ACTION_DONE, bytes((sequence,))))
        self.controller.poll()

        self.assertEqual(self.controller.counts[WasteType.RECYCLABLE], 1)
        self.assertEqual(self.transport.sent[1].command, Command.START_COMPRESS)
        self.assertEqual(self.controller.state, SystemState.COMPRESSING)

        compress_sequence = self.transport.sent[1].payload[0]
        self.transport.feed(Packet(Command.ACTION_DONE, bytes((compress_sequence,))))
        self.controller.poll()
        self.assertEqual(self.controller.state, SystemState.COOLDOWN)


if __name__ == "__main__":
    unittest.main()
