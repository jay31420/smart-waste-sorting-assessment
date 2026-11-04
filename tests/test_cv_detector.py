import unittest
from pathlib import Path

import numpy as np

from app.detectors import YoloDetector
from app.frame_sources import create_frame_source
from app.protocol import WasteType


class VideoSourceTests(unittest.TestCase):
    def test_assessment_video_can_be_read_and_restarted(self):
        video = Path("assets/assessment_demo.mp4")
        self.assertTrue(video.is_file())
        source = create_frame_source("video", str(video))
        try:
            ok, frame = source.read()
            self.assertTrue(ok)
            self.assertEqual(frame.shape[:2], (720, 1280))
            self.assertGreater(source.frame_count, 300)
            self.assertTrue(source.restart())
            ok, restarted = source.read()
            self.assertTrue(ok)
            self.assertEqual(restarted.shape, frame.shape)
        finally:
            source.release()

    def test_synthetic_source_is_not_available(self):
        with self.assertRaises(ValueError):
            create_frame_source("synthetic")


class _Scalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class _Coordinates:
    def __init__(self, values):
        self.values = np.array(values)

    def cpu(self):
        return self

    def numpy(self):
        return self.values


class _Box:
    conf = _Scalar(0.91)
    cls = _Scalar(0)
    xyxy = [_Coordinates([10, 20, 80, 120])]


class _Result:
    names = {0: "battery"}
    boxes = [_Box()]


class _FakeYolo:
    names = {0: "battery"}

    def __init__(self):
        self.calls = []

    def predict(self, **kwargs):
        self.calls.append(kwargs)
        return [_Result()]


class YoloAdapterTests(unittest.TestCase):
    def test_yolo_api_is_adapted_without_loading_real_weights(self):
        fake_model = _FakeYolo()
        detector = YoloDetector(model=fake_model)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        output = detector.detect(frame)
        self.assertEqual(output[0].waste_type, WasteType.HAZARDOUS)
        self.assertEqual(output[0].box, (10, 20, 80, 120))
        self.assertIs(fake_model.calls[0]["source"], frame)

    def test_unknown_model_class_is_rejected(self):
        model = _FakeYolo()
        model.names = {0: "not-configured"}
        with self.assertRaises(ValueError):
            YoloDetector(model=model)


if __name__ == "__main__":
    unittest.main()
