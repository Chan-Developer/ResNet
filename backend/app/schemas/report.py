from typing import Optional

from pydantic import BaseModel, Field


class DiseaseDistributionItem(BaseModel):
    label: str
    display_name: str
    count: int
    ratio: float


class RegionDistributionItem(BaseModel):
    region_code: str
    total_count: int
    ratio: float
    has_alert: bool = False
    has_unread_alert: bool = False


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
    region_code: Optional[str] = None
    prediction_count: int
    confirmed_count: int
    avg_confidence: Optional[float] = None
    accuracy: Optional[float] = None


class DashboardOverviewOut(BaseModel):
    summary: DashboardSummary
    distribution: list[DiseaseDistributionItem]
    trend: list[TrendPoint]
    region_distribution: list[RegionDistributionItem] = Field(default_factory=list)


class DashboardFilterOptionsOut(BaseModel):
    crops: list[str]
    labels: list[dict[str, str]]
    regions: list[str] = Field(default_factory=list)
