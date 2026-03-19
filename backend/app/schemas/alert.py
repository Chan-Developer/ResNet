from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


AlertStatus = Literal["unread", "read"]


class RegionAlertOut(BaseModel):
    id: int
    region_code: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    confirmed_label: str
    display_name: str
    current_count: int
    previous_count: int
    growth_rate: float
    threshold: float
    window_days: int
    status: AlertStatus
    message: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RegionAlertSummaryOut(BaseModel):
    unread_count: int
    total_count: int
