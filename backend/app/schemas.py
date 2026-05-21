"""Pydantic models for the Fleet Safety Review Platform."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["driver", "reviewer", "manager"]
CaseStatus = Literal["new", "processing", "review", "approved", "dismissed", "escalated", "failed"]
EventStatus = Literal["pending", "approved", "dismissed", "escalated"]


class UserRead(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    driver_id: str | None = None
    created_at: str


class DriverRead(BaseModel):
    id: str
    name: str
    employee_id: str
    vehicle_id: str | None = None
    risk_score: int
    total_events: int = 0
    approved_events: int = 0
    dismissed_events: int = 0
    escalated_events: int = 0
    created_at: str


class DetectedEventRead(BaseModel):
    id: str
    case_id: str
    event_type: str
    timestamp_seconds: float
    severity: str
    confidence: float
    description: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: EventStatus
    dismissal_reason: str | None = None
    escalation_notes: str | None = None
    reviewer_id: str | None = None
    reviewed_at: str | None = None
    created_at: str


class DriverCommentRead(BaseModel):
    id: int
    case_id: str
    driver_id: str
    text: str
    created_at: str


class CaseRead(BaseModel):
    id: str
    driver_id: str
    reviewer_id: str | None = None
    video_filename: str
    status: CaseStatus
    progress: int
    ai_summary: str | None = None
    brief: dict[str, Any] | None = None
    reviewer_notes: str | None = None
    error: str | None = None
    created_at: str
    updated_at: str
    events: list[DetectedEventRead] = Field(default_factory=list)
    driver: DriverRead | None = None
    comments: list[DriverCommentRead] = Field(default_factory=list)


class CoachingRead(BaseModel):
    id: str
    driver_id: str
    case_id: str | None = None
    recommendation_text: str
    reason: str
    acknowledged: bool = False
    acknowledged_at: str | None = None
    created_at: str


class UploadResponse(BaseModel):
    case_id: str
    status: str


class DismissPayload(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class EscalatePayload(BaseModel):
    notes: str = Field(min_length=1, max_length=500)


class FinalizePayload(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class DriverCommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ProgressMessage(BaseModel):
    case_id: str
    status: str
    progress: int
    message: str


class AnalyticsSummary(BaseModel):
    total_cases: int
    reviewed_cases: int
    pending_escalations: int
    false_positive_rate: float
    most_common_event: str | None
    high_risk_drivers: list[dict[str, Any]]
