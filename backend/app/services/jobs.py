from __future__ import annotations

from pathlib import Path

from app.database import save_report_result, update_report_progress
from app.services.progress import progress_manager
from app.services.video_processor import process_video


async def run_processing_job(report_id: str, video_path: Path) -> None:
    async def publish(status: str, progress: int, message: str) -> None:
        update_report_progress(report_id, status, progress)
        await progress_manager.publish(report_id, status, progress, message)

    try:
        await publish("processing", 3, "Upload received. Preparing video analysis.")
        events, brief = await process_video(video_path, publish)
        save_report_result(report_id, events, brief)
        await progress_manager.publish(report_id, "complete", 100, "Report saved.")
    except Exception as exc:
        update_report_progress(report_id, "failed", 100, str(exc))
        await progress_manager.publish(report_id, "failed", 100, f"Processing failed: {exc}")
