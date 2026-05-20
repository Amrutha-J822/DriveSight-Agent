from typing import Any, Literal

from pydantic import BaseModel, Field


FeedbackAction = Literal["approve", "dismiss", "escalate"]


class UploadResponse(BaseModel):
    report_id: str
    status: str


class FeedbackCreate(BaseModel):
    action: FeedbackAction
    note: str | None = Field(default=None, max_length=500)


class FeedbackRead(BaseModel):
    id: int
    report_id: str
    action: FeedbackAction
    note: str | None
    created_at: str


class ReportRead(BaseModel):
    id: str
    filename: str
    status: str
    progress: int
    verdict: str | None = None
    confidence: float | None = None
    brief: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    feedback: list[FeedbackRead] = Field(default_factory=list)
    error: str | None = None
    created_at: str
    updated_at: str


class ProgressMessage(BaseModel):
    report_id: str
    status: str
    progress: int
    message: str
