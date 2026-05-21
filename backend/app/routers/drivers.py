from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.database import (
    acknowledge_coaching,
    delete_driver as db_delete_driver,
    get_driver,
    insert_driver,
    insert_driver_comment,
    list_cases,
    list_coaching,
    list_drivers,
    update_driver as db_update_driver,
)
from app.schemas import (
    CaseRead,
    CoachingRead,
    DriverCommentCreate,
    DriverCommentRead,
    DriverCreate,
    DriverRead,
    DriverUpdate,
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


@router.post("", response_model=DriverRead, status_code=201)
def create_driver(
    payload: DriverCreate,
    _: CurrentUser = Depends(require_roles("manager")),
) -> dict:
    driver_id = f"drv_{uuid4().hex[:10]}"
    try:
        return insert_driver(driver_id, payload.name, payload.employee_id, payload.vehicle_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not create driver: {exc}")


@router.patch("/{driver_id}", response_model=DriverRead)
def update_driver_route(
    driver_id: str,
    payload: DriverUpdate,
    _: CurrentUser = Depends(require_roles("manager")),
) -> dict:
    if not get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    return db_update_driver(driver_id, payload.name, payload.employee_id, payload.vehicle_id)


@router.delete("/{driver_id}", status_code=204)
def delete_driver_route(
    driver_id: str,
    _: CurrentUser = Depends(require_roles("manager")),
) -> None:
    if not get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    try:
        db_delete_driver(driver_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete driver — they still have cases or users linked. ({exc})",
        )


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
