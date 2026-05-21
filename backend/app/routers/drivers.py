from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.database import (
    acknowledge_coaching,
    get_driver,
    insert_driver_comment,
    list_cases,
    list_coaching,
    list_drivers,
)
from app.schemas import (
    CaseRead,
    CoachingRead,
    DriverCommentCreate,
    DriverCommentRead,
    DriverRead,
)
from app.services.auth import (
    CurrentUser,
    assert_can_access_driver,
    get_current_user,
    require_roles,
)

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverRead])
def drivers(_: CurrentUser = Depends(require_roles("reviewer", "manager"))) -> list[dict]:
    return list_drivers()


@router.get("/{driver_id}", response_model=DriverRead)
def driver_detail(driver_id: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    assert_can_access_driver(user, driver_id, allowed_roles={"reviewer", "manager"})
    driver = get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.get("/{driver_id}/cases", response_model=list[CaseRead])
def driver_cases(driver_id: str, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    assert_can_access_driver(user, driver_id, allowed_roles={"reviewer", "manager"})
    return list_cases(driver_id=driver_id)


@router.get("/{driver_id}/coaching", response_model=list[CoachingRead])
def driver_coaching(driver_id: str, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    assert_can_access_driver(user, driver_id, allowed_roles={"reviewer", "manager"})
    return [
        {**rec, "acknowledged": bool(rec["acknowledged"])} for rec in list_coaching(driver_id)
    ]


@router.post("/{driver_id}/coaching/{rec_id}/acknowledge")
def acknowledge(driver_id: str, rec_id: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    assert_can_access_driver(user, driver_id, allowed_roles={"reviewer", "manager"})
    acknowledge_coaching(rec_id)
    return {"ok": True}


@router.post("/{driver_id}/cases/{case_id}/comment", response_model=DriverCommentRead)
def add_comment(
    driver_id: str,
    case_id: str,
    payload: DriverCommentCreate,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    # Only the driver themselves can add a driver comment.
    if user["role"] != "driver" or user.get("driver_id") != driver_id:
        raise HTTPException(status_code=403, detail="Only the driver of this case can add a driver comment.")
    return insert_driver_comment(case_id, driver_id, payload.text)
