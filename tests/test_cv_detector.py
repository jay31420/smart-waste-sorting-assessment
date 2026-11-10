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

    def test_original_project_video_supports_seek_and_restart(self):
        video = Path("vedio/dep.mp4")
        self.assertTrue(video.is_file())
        source = create_frame_source("video", str(video))
        try:
            self.assertEqual(source.frame_count, 2839)
            self.assertAlmostEqual(source.source_fps, 30.0, places=1)
            ok, first = source.read()
            self.assertTrue(ok)
            self.assertEqual(first.shape[:2], (720, 1280))
            self.assertTrue(source.seek_frame(100))
            ok, later = source.read()
            self.assertTrue(ok)
            self.assertEqual(later.shape, first.shape)
            self.assertFalse(source.seek_frame(-1))
            self.assertFalse(source.seek_frame(source.frame_count))
            self.assertTrue(source.restart())
            self.assertLessEqual(source.current_frame, 1)

            self.assertTrue(source.seek_frame(source.frame_count - 1))
            ok, _ = source.read()
            self.assertTrue(ok)
            ok, frame = source.read()
            self.assertFalse(ok)
            self.assertIsNone(frame)
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


class _MultiBoxResult:
    names = {0: "battery", 1: "box"}

    def __init__(self):
        self.boxes = [
            type("Box", (), {"conf": _Scalar(0.65), "cls": _Scalar(1), "xyxy": [_Coordinates([1, 2, 3, 4])]})(),
            type("Box", (), {"conf": _Scalar(0.91), "cls": _Scalar(0), "xyxy": [_Coordinates([10, 20, 80, 90])]})(),
            type("Box", (), {"conf": _Scalar(0.20), "cls": _Scalar(1), "xyxy": [_Coordinates([0, 0, 1, 1])]})(),
        ]


class _MultiBoxYolo:
    names = _MultiBoxResult.names

    def predict(self, **kwargs):
        return [_MultiBoxResult()]


class YoloAdapterTests(unittest.TestCase):
    def test_yolo_api_is_adapted_without_loading_real_weights(self):
        fake_model = _FakeYolo()
        detector = YoloDetector(model=fake_model)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        output = detector.detect(frame)
        self.assertEqual(output[0].waste_type, WasteType.HAZARDOUS)
        self.assertEqual(output[0].box, (10, 20, 80, 120))
        self.assertIs(fake_model.calls[0]["source"], frame)

    def test_detections_are_filtered_and_sorted_by_confidence(self):
        detector = YoloDetector(model=_MultiBoxYolo())
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        output = detector.detect(frame)
        self.assertEqual([item.class_name for item in output], ["battery", "box"])
        self.assertEqual([item.confidence for item in output], [0.91, 0.65])

    def test_unknown_model_class_is_rejected(self):
        model = _FakeYolo()
        model.names = {0: "not-configured"}
        with self.assertRaises(ValueError):
            YoloDetector(model=model)


if __name__ == "__main__":
    unittest.main()
