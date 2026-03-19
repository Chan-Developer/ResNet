from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from .prediction import PredictionItem


class EvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: Literal["knowledge", "case"]
    title: str
    source_name: str
    snippet: str
    score: float
    url: str = ""


class AdviceCitation(BaseModel):
    evidence_id: str
    title: str
    source_name: str


class AdviceOut(BaseModel):
    summary: str
    condition_overview: str
    recommended_actions: List[str]
    uncertainty_notice: str
    follow_up: str
    citations: List[AdviceCitation]


class SimilarCaseOut(BaseModel):
    case_id: int
    similarity: float
    confirmed_label: str
    display_name: str
    summary: str
    reference_actions: List[str]
    created_at: Optional[datetime] = None


class DiagnosisDraftOut(BaseModel):
    draft_token: str
    image_url: str
    image_filename: str
    crop_name: str
    health_status: Literal["healthy", "diseased"]
    top_k: int
    predictions: List[PredictionItem]
    best_prediction: Optional[PredictionItem] = None
    knowledge_evidence: List[EvidenceItem]
    similar_cases: List[SimilarCaseOut]
    advice: AdviceOut


class ConfirmDiagnosisIn(BaseModel):
    draft_token: str
    confirmed_label: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class CaseOut(BaseModel):
    id: int
    prediction_record_id: int
    image_url: str
    image_filename: str
    predicted_label: str
    predicted_display_name: str
    confirmed_label: str
    confirmed_display_name: str
    crop_name: str
    disease_name: str
    health_status: str
    confidence: float
    status: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    region_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    advice: AdviceOut
    evidence: List[EvidenceItem]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CaseConfirmOut(BaseModel):
    case: CaseOut
    similar_cases: List[SimilarCaseOut]
