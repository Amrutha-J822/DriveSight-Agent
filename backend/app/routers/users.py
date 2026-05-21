from __future__ import annotations

from fastapi import APIRouter, Depends

from app.database import list_users
from app.schemas import UserRead
from app.services.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserRead])
def all_users() -> list[dict]:
    """Public list for the mock login picker. In Phase 2 this becomes admin-only."""
    return list_users()


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return user
