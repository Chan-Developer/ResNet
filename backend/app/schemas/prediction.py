from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class PredictionItem(BaseModel):
    class_index: int
    class_name: str
    display_name: str
    confidence: float


class PredictResponse(BaseModel):
    top_k: int
    predictions: List[PredictionItem]
    best_prediction: Optional[PredictionItem] = None

class HistoryOut(BaseModel):
    id: int
    image_filename: str
    image_url: str
    top1_class: str
    top1_confidence: float
    top_k: int
    results_json: Any
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
