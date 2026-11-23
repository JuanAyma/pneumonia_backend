from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.enums import RiskLevel

class DiagnosticRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    diagnosis_id: str
    s3_key: str
    normalized_path: str
    specialization_id: str
    model_version: str = 'latest'

class ClassLabel(BaseModel):
    index: int
    label: str
    confidence: float

class GradCamResult(BaseModel):
    heatmap_s3_key: str
    heatmap_url: str
    top_regions: List[str]

class DiagnosticResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    diagnosis_id: str
    prediction: ClassLabel
    all_labels: List[ClassLabel]
    has_pathology: bool
    risk_level: RiskLevel
    grad_cam: GradCamResult
    model_version: str
    inference_ms: int
