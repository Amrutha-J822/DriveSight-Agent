"""Safety review case endpoints — uploads, lists, per-event decisions, and finalize."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.config import UPLOAD_DIR
from app.database import (
    adjust_driver_counters,
    create_case,
    get_case,
    get_driver,
    get_event,
    insert_coaching,
    list_cases,
    set_case_status,
    update_event_decision,
)
from app.schemas import (
    CaseRead,
    DetectedEventRead,
    DismissPayload,
    EscalatePayload,
    FinalizePayload,
    UploadResponse,
)
from app.services.auth import CurrentUser, get_current_user, require_roles
from app.services.coaching import build_coaching
from app.services.jobs import run_processing_job


router = APIRouter(prefix="/api/cases", tags=["cases"])


# Risk score deltas per decision — adjust here to tune driver scoring math.
RISK_DELTAS = {
    "approved": 10,
    "dismissed": 0,
    "escalated": 25,
}


def _safe_filename(filename: str) -> str:
    keep = [c for c in filename if c.isalnum() or c in {".", "_", "-"}]
    return "".join(keep) or "dashcam-video"


def _load_case_or_404(case_id: str) -> dict:
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# ---------------------------------------------------------------------------
# Listing + detail
# ---------------------------------------------------------------------------


@router.get("", response_model=list[CaseRead])
def cases(user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    if user["role"] == "driver":
        return list_cases(driver_id=user.get("driver_id"))
    return list_cases()


@router.get("/{case_id}", response_model=CaseRead)
def case_detail(case_id: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    case = _load_case_or_404(case_id)
    if user["role"] == "driver" and user.get("driver_id") != case["driver_id"]:
        raise HTTPException(status_code=403, detail="Drivers can only view their own cases.")
    return case


# ---------------------------------------------------------------------------
# Upload (reviewers + managers)
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=UploadResponse)
async def upload_case(
    background_tasks: BackgroundTasks,
    driver_id: str = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_roles("reviewer", "manager")),
) -> UploadResponse:
    if not get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")

    case_id = f"case_{uuid4().hex[:12]}"
    filename = _safe_filename(file.filename or "dashcam-video")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target_path = Path(UPLOAD_DIR) / f"{case_id}_{filename}"

    with target_path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            output.write(chunk)

    create_case(case_id, driver_id, user["id"], filename)
    background_tasks.add_task(run_processing_job, case_id, target_path)
    return UploadResponse(case_id=case_id, status="processing")


# ---------------------------------------------------------------------------
# Per-event decisions — Approve / Dismiss / Escalate
# ---------------------------------------------------------------------------


def _decide_event(
    case_id: str,
    event_id: str,
    *,
    new_status: str,
    user: CurrentUser,
    dismissal_reason: str | None = None,
    escalation_notes: str | None = None,
) -> dict:
    case = _load_case_or_404(case_id)
    event = get_event(event_id)
    if not event or event["case_id"] != case_id:
        raise HTTPException(status_code=404, detail="Event not found on this case")

    previous_status = event["status"]
    if previous_status == new_status:
        return get_event(event_id) or {}

    update_event_decision(
        event_id,
        status=new_status,
        reviewer_id=user["id"],
        dismissal_reason=dismissal_reason,
        escalation_notes=escalation_notes,
    )

    # Reverse the previous decision's effects on the driver before applying the new one.
    if previous_status in RISK_DELTAS:
        adjust_driver_counters(
            case["driver_id"],
            risk_delta=-RISK_DELTAS[previous_status],
            approved_delta=-1 if previous_status == "approved" else 0,
            dismissed_delta=-1 if previous_status == "dismissed" else 0,
            escalated_delta=-1 if previous_status == "escalated" else 0,
            total_delta=-1,
        )

    adjust_driver_counters(
        case["driver_id"],
        risk_delta=RISK_DELTAS[new_status],
        approved_delta=1 if new_status == "approved" else 0,
        dismissed_delta=1 if new_status == "dismissed" else 0,
        escalated_delta=1 if new_status == "escalated" else 0,
        total_delta=1,
    )

    return get_event(event_id) or {}


@router.post("/{case_id}/events/{event_id}/approve", response_model=DetectedEventRead)
def approve_event(
    case_id: str,
    event_id: str,
    user: CurrentUser = Depends(require_roles("reviewer", "manager")),
) -> dict:
    return _decide_event(case_id, event_id, new_status="approved", user=user)


@router.post("/{case_id}/events/{event_id}/dismiss", response_model=DetectedEventRead)
def dismiss_event(
    case_id: str,
    event_id: str,
    payload: DismissPayload,
    user: CurrentUser = Depends(require_roles("reviewer", "manager")),
) -> dict:
    return _decide_event(
        case_id, event_id,
        new_status="dismissed",
        user=user,
        dismissal_reason=payload.reason,
    )


@router.post("/{case_id}/events/{event_id}/escalate", response_model=DetectedEventRead)
def escalate_event(
    case_id: str,
    event_id: str,
    payload: EscalatePayload,
    user: CurrentUser = Depends(require_roles("reviewer", "manager")),
) -> dict:
    return _decide_event(
        case_id, event_id,
        new_status="escalated",
        user=user,
        escalation_notes=payload.notes,
    )


# ---------------------------------------------------------------------------
# Finalize a case — rolls up event decisions into a case status + coaching brief
# ---------------------------------------------------------------------------


@router.post("/{case_id}/finalize", response_model=CaseRead)
def finalize_case(
    case_id: str,
    payload: FinalizePayload,
    user: CurrentUser = Depends(require_roles("reviewer", "manager")),
) -> dict:
    case = _load_case_or_404(case_id)
    events = case.get("events") or []

    pending = [e for e in events if e["status"] == "pending"]
    if pending:
        raise HTTPException(
            status_code=400,
            detail=f"{len(pending)} event(s) still pending. Decide on all events before finalizing.",
        )

    # Roll-up: any escalated → escalated; else any approved → approved; else dismissed.
    if any(e["status"] == "escalated" for e in events):
        case_status = "escalated"
    elif any(e["status"] == "approved" for e in events):
        case_status = "approved"
    else:
        case_status = "dismissed"

    set_case_status(case_id, case_status, payload.notes)

    coaching = build_coaching(case)
    if coaching:
        insert_coaching(
            rec_id=f"coa_{uuid4().hex[:12]}",
            driver_id=case["driver_id"],
            case_id=case_id,
            text=coaching["recommendation_text"],
            reason=coaching["reason"],
        )

    return _load_case_or_404(case_id)
