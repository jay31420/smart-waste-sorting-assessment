"""YOLO 检测器适配与统一结果类型。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from .protocol import WasteType


@dataclass
class Detection:
    waste_type: WasteType
    class_name: str
    confidence: float
    box: Tuple[int, int, int, int]


class Detector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[Detection]:
        raise NotImplementedError


class YoloDetector(Detector):
    """加载指定权重，并把模型原始类别映射到四类垃圾。"""

    DEFAULT_CLASS_MAP = {
        "bottolad": WasteType.RECYCLABLE,
        "plasticbottle": WasteType.RECYCLABLE,
        "box": WasteType.RECYCLABLE,
        "can": WasteType.RECYCLABLE,
        "papercup": WasteType.RECYCLABLE,
        "yangleduo": WasteType.RECYCLABLE,
        "potato": WasteType.KITCHEN,
        "carrot": WasteType.KITCHEN,
        "qincarrot": WasteType.KITCHEN,
        "redcarrot": WasteType.KITCHEN,
        "whitcarrot": WasteType.KITCHEN,
        "battery": WasteType.HAZARDOUS,
        "drug": WasteType.HAZARDOUS,
        "cobblestone": WasteType.OTHER,
        "porcelain": WasteType.OTHER,
    }

    def __init__(
        self,
        weights: Optional[str] = None,
        model=None,
        confidence: float = 0.50,
        device: Optional[str] = None,
    ) -> None:
        if not 0.0 < confidence <= 1.0:
            raise ValueError("置信度阈值必须在 (0, 1] 范围内")
        if model is None:
            if not weights:
                raise ValueError("必须指定 YOLO 权重文件")
            weight_path = Path(weights)
            if not weight_path.is_file():
                raise FileNotFoundError("YOLO 权重不存在：{}".format(weight_path))
            try:
                import torch
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("未安装 YOLO 运行环境") from exc
            self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
            self.model = YOLO(str(weight_path))
        else:
            self.model = model
            self.device = device or "cpu"

        self.confidence = confidence
        model_names = getattr(self.model, "names", {})
        names = model_names.values() if isinstance(model_names, dict) else model_names
        unknown = sorted(set(names) - set(self.DEFAULT_CLASS_MAP))
        if unknown:
            raise ValueError("权重中存在未配置类别：{}".format(", ".join(unknown)))

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """调用 YOLO 并将其框结果转换为项目内部的数据结构。"""
        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )
        detections = []  # type: List[Detection]

        for result in results or []:
            names = getattr(result, "names", None) or getattr(self.model, "names", {})
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                confidence = self._scalar(getattr(box, "conf", 0.0))
                if not np.isfinite(confidence) or confidence < self.confidence:
                    continue

                class_id = int(self._scalar(getattr(box, "cls", -1)))
                class_name = self._class_name(names, class_id)
                waste_type = self.DEFAULT_CLASS_MAP.get(class_name)
                if waste_type is None:
                    continue

                coordinates = getattr(box, "xyxy", None)
                if coordinates is None:
                    continue
                if isinstance(coordinates, (list, tuple)):
                    if not coordinates:
                        continue
                    coordinates = coordinates[0]
                elif getattr(coordinates, "ndim", 0) > 1:
                    coordinates = coordinates[0]
                if hasattr(coordinates, "cpu"):
                    coordinates = coordinates.cpu()
                if hasattr(coordinates, "numpy"):
                    coordinates = coordinates.numpy()
                coordinates = np.asarray(coordinates).reshape(-1)
                if coordinates.size < 4:
                    continue

                x1, y1, x2, y2 = (int(float(value)) for value in coordinates[:4])
                detections.append(
                    Detection(
                        waste_type=waste_type,
                        class_name=class_name,
                        confidence=confidence,
                        box=(x1, y1, x2, y2),
                    )
                )

        detections.sort(key=lambda detection: detection.confidence, reverse=True)
        return detections

    @staticmethod
    def _scalar(value) -> float:
        if hasattr(value, "item"):
            value = value.item()
        return float(value)

    @staticmethod
    def _class_name(names, class_id: int) -> str:
        try:
            name = names[class_id]
        except (IndexError, KeyError, TypeError):
            return ""
        return str(name)
