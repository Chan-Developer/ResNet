from typing import Optional

from pydantic import BaseModel


class DiseaseDistributionItem(BaseModel):
    label: str
    display_name: str
    count: int
    ratio: float


class TrendPoint(BaseModel):
    date: str
    prediction_count: int
    confirmed_count: int
    accuracy: Optional[float] = None


class DashboardSummary(BaseModel):
    scope: str
    period_days: int
    start_date: str
    end_date: str
    crop_name: Optional[str] = None
    label: Optional[str] = None
    prediction_count: int
    confirmed_count: int
    avg_confidence: Optional[float] = None
    accuracy: Optional[float] = None


class DashboardOverviewOut(BaseModel):
    summary: DashboardSummary
    distribution: list[DiseaseDistributionItem]
    trend: list[TrendPoint]


class DashboardFilterOptionsOut(BaseModel):
    crops: list[str]
    labels: list[dict[str, str]]
