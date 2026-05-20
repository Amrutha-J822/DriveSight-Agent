from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.config import UPLOAD_DIR
from app.database import add_feedback, create_report, get_report, list_reports
from app.schemas import FeedbackCreate, FeedbackRead, ReportRead, UploadResponse
from app.services.jobs import run_processing_job

router = APIRouter(prefix="/api/reports", tags=["reports"])


def safe_filename(filename: str) -> str:
    keep = [character for character in filename if character.isalnum() or character in {".", "_", "-"}]
    return "".join(keep) or "dashcam-video"


@router.post("/upload", response_model=UploadResponse)
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> UploadResponse:
    report_id = str(uuid4())
    filename = safe_filename(file.filename or "dashcam-video")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target_path = Path(UPLOAD_DIR) / f"{report_id}_{filename}"

    with target_path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            output.write(chunk)

    create_report(report_id, filename)
    background_tasks.add_task(run_processing_job, report_id, target_path)
    return UploadResponse(report_id=report_id, status="queued")


@router.get("", response_model=list[ReportRead])
def reports() -> list[dict]:
    return list_reports()


@router.get("/{report_id}", response_model=ReportRead)
def report_detail(report_id: str) -> dict:
    report = get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/feedback", response_model=FeedbackRead)
def create_feedback(report_id: str, payload: FeedbackCreate) -> dict:
    if not get_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return add_feedback(report_id, payload.action, payload.note)
