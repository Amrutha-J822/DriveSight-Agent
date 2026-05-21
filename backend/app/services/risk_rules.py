from __future__ import annotations

from typing import Any

import cv2
import numpy as np


VEHICLE_LABELS = {"car", "truck", "bus", "motorcycle"}


DEFAULT_CONFIDENCE = {
    "vehicle_detected": 0.7,
    "pedestrian_detected": 0.75,
    "stop_sign_detected": 0.6,
    "close_following_approximation": 0.65,
    "lane_drift_placeholder": 0.55,
    "no_major_events_detected": 0.95,
}


def make_event(
    event_type: str,
    timestamp_seconds: float,
    severity: str,
    description: str,
    evidence: dict[str, Any],
    confidence: float | None = None,
) -> dict[str, Any]:
    return {
        "type": event_type,
        "timestamp_seconds": round(timestamp_seconds, 2),
        "severity": severity,
        "confidence": confidence if confidence is not None else DEFAULT_CONFIDENCE.get(event_type, 0.6),
        "description": description,
        "evidence": evidence,
    }


def extract_detection_events(
    timestamp_seconds: float,
    detections: list[dict[str, Any]],
    frame_shape: tuple[int, int, int],
) -> list[dict[str, Any]]:
    height, width = frame_shape[:2]
    events: list[dict[str, Any]] = []

    vehicles = [d for d in detections if d["label"] in VEHICLE_LABELS]
    pedestrians = [d for d in detections if d["label"] == "person"]
    stop_signs = [d for d in detections if d["label"] == "stop sign"]

    if vehicles:
        events.append(
            make_event(
                "vehicle_detected",
                timestamp_seconds,
                "info",
                f"{len(vehicles)} vehicle-like object(s) detected.",
                {"count": len(vehicles), "detections": vehicles[:5]},
            )
        )

    if pedestrians:
        events.append(
            make_event(
                "pedestrian_detected",
                timestamp_seconds,
                "high",
                f"{len(pedestrians)} pedestrian(s) detected near the driving scene.",
                {"count": len(pedestrians), "detections": pedestrians[:5]},
            )
        )

    if stop_signs:
        events.append(
            make_event(
                "stop_sign_detected",
                timestamp_seconds,
                "medium",
                "Stop sign candidate detected.",
                {"count": len(stop_signs), "detections": stop_signs[:3]},
            )
        )

    for detection in vehicles:
        x1, y1, x2, y2 = detection["bbox"]
        box_area_ratio = ((x2 - x1) * (y2 - y1)) / max(width * height, 1)
        lower_frame = y2 > height * 0.58
        if box_area_ratio > 0.14 and lower_frame:
            events.append(
                make_event(
                    "close_following_approximation",
                    timestamp_seconds,
                    "high",
                    "Large vehicle box low in the frame suggests possible close following.",
                    {
                        "box_area_ratio": round(box_area_ratio, 3),
                        "detection": detection,
                        "rule": "vehicle box covers >14% of frame and reaches lower driving area",
                    },
                )
            )
            break

    return events


def estimate_lane_drift_placeholder(frame: np.ndarray, timestamp_seconds: float) -> dict[str, Any] | None:
    """Simple lane-center approximation. Treat this as a placeholder, not a safety-grade lane model."""
    height, width = frame.shape[:2]
    region = frame[int(height * 0.55) : height, :]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=45, minLineLength=40, maxLineGap=80)
    if lines is None:
        return None

    left_lines: list[tuple[int, int, int, int]] = []
    right_lines: list[tuple[int, int, int, int]] = []
    for line in lines[:, 0]:
        x1, y1, x2, y2 = [int(value) for value in line]
        if x2 == x1:
            continue
        slope = (y2 - y1) / (x2 - x1)
        if slope < -0.35:
            left_lines.append((x1, y1, x2, y2))
        elif slope > 0.35:
            right_lines.append((x1, y1, x2, y2))

    if not left_lines or not right_lines:
        return None

    left_x = int(np.mean([max(x1, x2) for x1, _, x2, _ in left_lines]))
    right_x = int(np.mean([min(x1, x2) for x1, _, x2, _ in right_lines]))
    lane_center = (left_x + right_x) / 2
    vehicle_center = width / 2
    offset_ratio = abs(vehicle_center - lane_center) / width

    if offset_ratio > 0.16:
        direction = "left" if vehicle_center < lane_center else "right"
        return make_event(
            "lane_drift_placeholder",
            timestamp_seconds,
            "medium",
            f"Placeholder lane logic suggests the vehicle may be drifting {direction}.",
            {
                "offset_ratio": round(offset_ratio, 3),
                "left_lane_x": left_x,
                "right_lane_x": right_x,
                "note": "Replace with a dedicated lane segmentation model before production use.",
            },
        )
    return None


def deduplicate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    last_seen: dict[str, float] = {}
    minimum_gap_seconds = {
        "vehicle_detected": 4,
        "pedestrian_detected": 2,
        "stop_sign_detected": 5,
        "close_following_approximation": 3,
        "lane_drift_placeholder": 6,
    }

    for event in events:
        event_type = event["type"]
        timestamp = event["timestamp_seconds"]
        if timestamp - last_seen.get(event_type, -999) < minimum_gap_seconds.get(event_type, 2):
            continue
        last_seen[event_type] = timestamp
        deduped.append(event)
    return deduped
