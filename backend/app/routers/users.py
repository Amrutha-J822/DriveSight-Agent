from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.database import (
    delete_user as db_delete_user,
    get_user,
    insert_user,
    list_users,
    update_user as db_update_user,
)
from app.schemas import UserCreate, UserRead, UserUpdate
from app.services.auth import CurrentUser, get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserRead])
def all_users() -> list[dict]:
    """Public list for the mock login picker. In Phase 2 this becomes admin-only."""
    return list_users()


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return user


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    _: CurrentUser = Depends(require_roles("manager")),
) -> dict:
    user_id = f"usr_{uuid4().hex[:10]}"
    try:
        return insert_user(user_id, payload.name, payload.email, payload.role, payload.driver_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not create user: {exc}")


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user_route(
    user_id: str,
    payload: UserUpdate,
    _: CurrentUser = Depends(require_roles("manager")),
) -> dict:
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return db_update_user(user_id, payload.name, payload.email, payload.role, payload.driver_id)


@router.delete("/users/{user_id}", status_code=204)
def delete_user_route(
    user_id: str,
    actor: CurrentUser = Depends(require_roles("manager")),
) -> None:
    if user_id == actor["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    db_delete_user(user_id)
