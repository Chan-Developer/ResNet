from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .prediction import PredictionItem

PlanStatus = Literal["active", "paused", "completed", "cancelled"]
EffectStatus = Literal["improved", "stable", "worse", "unknown"]


class FollowUpPlanCreateIn(BaseModel):
    title: Optional[str] = None
    case_id: Optional[int] = None
    target_label: Optional[str] = None
    notes: Optional[str] = None
    frequency_days: int = Field(default=7, ge=1, le=90)
    start_date: Optional[date] = None


class FollowUpPlanUpdateIn(BaseModel):
    status: Optional[PlanStatus] = None
    frequency_days: Optional[int] = Field(default=None, ge=1, le=90)
    notes: Optional[str] = None


class FollowUpPlanOut(BaseModel):
    id: int
    user_id: int
    case_id: Optional[int] = None
    title: str
    target_label: str
    target_display_name: str
    notes: str
    frequency_days: int
    start_date: date
    next_review_date: date
    status: PlanStatus
    latest_effect: EffectStatus
    effect_score: Optional[float] = None
    checkin_count: int = 0
    last_checkin_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FollowUpCheckinOut(BaseModel):
    id: int
    plan_id: int
    image_filename: str
    image_url: str
    top1_label: str
    top1_display_name: str
    top1_confidence: float
    target_confidence: float
    target_confidence_delta: float
    top1_confidence_delta: float
    effect_status: EffectStatus
    effect_score: float
    llm_summary: str
    note: str
    predictions: list[PredictionItem]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FollowUpEvaluationPoint(BaseModel):
    date: str
    target_confidence: float
    effect_status: EffectStatus
    top1_label: str
    top1_display_name: str


class FollowUpEvaluationOut(BaseModel):
    total_checkins: int
    improved_count: int
    stable_count: int
    worse_count: int
    latest_effect: EffectStatus
    effect_score: Optional[float] = None
    avg_target_confidence_delta: Optional[float] = None
    trend: list[FollowUpEvaluationPoint]
