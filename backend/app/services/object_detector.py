from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.config import YOLO_MODEL_PATH


COCO_NAMES = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    11: "stop sign",
}


class ObjectDetector:
    """Small wrapper that uses YOLO when configured, otherwise OpenCV fallbacks."""

    def __init__(self) -> None:
        self.model: Any | None = None
        self.backend = "opencv-fallback"
        if YOLO_MODEL_PATH and Path(YOLO_MODEL_PATH).exists():
            try:
                from ultralytics import YOLO

                self.model = YOLO(YOLO_MODEL_PATH)
                self.backend = "yolo"
            except Exception:
                self.model = None

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        detections = self._detect_with_yolo(frame) if self.model else []
        detections.extend(self._detect_stop_sign_by_color(frame))
        return detections

    def _detect_with_yolo(self, frame: np.ndarray) -> list[dict[str, Any]]:
        results = self.model(frame, verbose=False)
        detections: list[dict[str, Any]] = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = COCO_NAMES.get(class_id, result.names.get(class_id, str(class_id)))
                if label not in {"person", "car", "motorcycle", "bus", "truck", "stop sign"}:
                    continue
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0]]
                detections.append(
                    {
                        "label": label,
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2, y2],
                        "source": "yolo",
                    }
                )
        return detections

    def _detect_stop_sign_by_color(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """Approximate red octagon detection for demos when YOLO is not configured."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red_a = np.array([0, 80, 80])
        upper_red_a = np.array([10, 255, 255])
        lower_red_b = np.array([170, 80, 80])
        upper_red_b = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_red_a, upper_red_a) | cv2.inRange(hsv, lower_red_b, upper_red_b)
        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections: list[dict[str, Any]] = []
        frame_area = frame.shape[0] * frame.shape[1]
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < frame_area * 0.001:
                continue
            perimeter = cv2.arcLength(contour, True)
            approximation = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            if 6 <= len(approximation) <= 10:
                x, y, width, height = cv2.boundingRect(approximation)
                detections.append(
                    {
                        "label": "stop sign",
                        "confidence": 0.45,
                        "bbox": [x, y, x + width, y + height],
                        "source": "opencv-red-shape",
                    }
                )
        return detections
