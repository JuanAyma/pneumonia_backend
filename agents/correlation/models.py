from pydantic import BaseModel
from typing import Any, List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.enums import RiskLevel

class CorrelationRequest(BaseModel):
    diagnosis_id: str
    specialization_id: str
    diagnostic: Any
    symptom_analysis: Any

class Finding(BaseModel):
    code: str
    description: str
    confidence: float
    source: str

class CorrelationResponse(BaseModel):
    diagnosis_id: str
    findings: List[Finding]
    final_risk: RiskLevel
    urgency_hours: int
    recommended_actions: List[str]
    correlation_score: float
