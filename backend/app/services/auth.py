"""Mock authentication for Phase 1.

The frontend stores the picked user in localStorage and sends the user id as
the ``X-User-Id`` request header. This is replaced with Firebase token
verification in Phase 2 — the dependency signature stays the same so routers
keep working.
"""

from __future__ import annotations

from typing import Iterable

from fastapi import Depends, Header, HTTPException, status

from app.database import get_user


class CurrentUser(dict):
    """Just a dict subclass so we can `Depends(...)` a typed user object."""


def get_current_user(x_user_id: str | None = Header(default=None)) -> CurrentUser:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header. Pick a user on the login screen.",
        )
    user = get_user(x_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown user id: {x_user_id}",
        )
    return CurrentUser(user)


def require_roles(*allowed: str):
    """Dependency factory that 403s unless the current user has one of the allowed roles."""

    def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' is not allowed. Required: {', '.join(allowed)}.",
            )
        return user

    return _dependency


def is_role(user: CurrentUser, *roles: str) -> bool:
    return user["role"] in roles


def assert_can_access_driver(user: CurrentUser, driver_id: str, *, allowed_roles: Iterable[str] = ()) -> None:
    """Drivers can only access their own resources; staff with allowed roles can access any."""
    if user["role"] in allowed_roles:
        return
    if user["role"] == "driver" and user.get("driver_id") == driver_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this driver's data.",
    )
