from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.database import insert_event, save_case_brief, update_case_progress
from app.services.progress import progress_manager
from app.services.video_processor import process_video


async def run_processing_job(case_id: str, video_path: Path) -> None:
    async def publish(status: str, progress: int, message: str) -> None:
        update_case_progress(case_id, status, progress)
        await progress_manager.publish(case_id, status, progress, message)

    try:
        await publish("processing", 3, "Upload received. Preparing video analysis.")
        events, brief = await process_video(video_path, publish)
        for event in events:
            insert_event(
                event_id=f"evt_{uuid4().hex[:12]}",
                case_id=case_id,
                event_type=event["type"],
                timestamp_seconds=event["timestamp_seconds"],
                severity=event["severity"],
                confidence=float(event.get("confidence", 0.6)),
                description=event["description"],
                evidence=event.get("evidence", {}),
            )
        save_case_brief(case_id, brief)
        await progress_manager.publish(case_id, "review", 100, "Case ready for reviewer.")
    except Exception as exc:
        update_case_progress(case_id, "failed", 100, str(exc))
        await progress_manager.publish(case_id, "failed", 100, f"Processing failed: {exc}")
