from pydantic import BaseModel
from typing import List, Union
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.enums import RiskLevel

class SymptomAnalysisRequest(BaseModel):
    diagnosis_id: str
    specialization_id: str
    symptoms: dict
    has_pathology: bool
    risk_level: RiskLevel

class SymptomAlert(BaseModel):
    field_id: str
    value: Union[float, bool]
    threshold: Union[float, bool]
    severity: str

class SymptomAnalysisResponse(BaseModel):
    diagnosis_id: str
    clinical_score: float
    alerts: List[SymptomAlert]
    adjusted_risk: RiskLevel
    summary: str
