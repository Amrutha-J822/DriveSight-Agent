from __future__ import annotations

from pathlib import Path
from typing import Awaitable, Callable

import cv2

from app.services.llm_client import create_driving_risk_brief
from app.services.object_detector import ObjectDetector
from app.services.risk_rules import (
    deduplicate_events,
    estimate_lane_drift_placeholder,
    extract_detection_events,
    make_event,
)


ProgressCallback = Callable[[str, int, str], Awaitable[None]]


async def process_video(video_path: Path, progress: ProgressCallback) -> tuple[list[dict], dict]:
    detector = ObjectDetector()
    await progress("processing", 8, f"Opened detector backend: {detector.backend}")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("OpenCV could not read this video file.")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30)
    sample_stride = max(int(fps), 1)
    events: list[dict] = []
    processed = 0

    await progress("processing", 12, "Scanning sampled frames for road objects and risk cues.")
    while True:
        ok, frame = capture.read()
        if not ok:
            break

        frame_index = int(capture.get(cv2.CAP_PROP_POS_FRAMES))
        if frame_index % sample_stride != 0:
            continue

        timestamp = frame_index / max(fps, 1)
        detections = detector.detect(frame)
        events.extend(extract_detection_events(timestamp, detections, frame.shape))

        if processed % 5 == 0:
            lane_event = estimate_lane_drift_placeholder(frame, timestamp)
            if lane_event:
                events.append(lane_event)

        processed += 1
        if frame_count:
            percent = 12 + int((frame_index / frame_count) * 68)
            await progress("processing", min(percent, 80), f"Processed frame {frame_index} of {frame_count}.")

    capture.release()

    if not events:
        events.append(
            make_event(
                "no_major_events_detected",
                0,
                "info",
                "No configured high-risk event was detected in sampled frames.",
                {"sampled_frames": processed},
            )
        )

    events = deduplicate_events(events)
    await progress("summarizing", 86, "Sending structured event JSON to the risk brief service.")
    brief = await create_driving_risk_brief(events)
    await progress("complete", 100, "Driving Risk Brief is ready.")
    return events, brief
