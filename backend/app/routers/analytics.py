from __future__ import annotations

from fastapi import APIRouter, Depends

from app.database import analytics_summary
from app.schemas import AnalyticsSummary
from app.services.auth import require_roles

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
def manager_dashboard(_=Depends(require_roles("manager", "reviewer"))) -> dict:
    return analytics_summary()
