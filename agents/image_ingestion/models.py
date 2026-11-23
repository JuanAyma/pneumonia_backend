from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.enums import ImageSource, RiskLevel

class ImageIngestionRequest(BaseModel):
    diagnosis_id: str
    image_base64: str
    source: ImageSource
    patient_id: str
    specialization_id: str

class ImageQualityFlags(BaseModel):
    is_grayscale: bool
    contrast_ok: bool
    resolution_ok: bool
    sharpness_score: float

class ImageIngestionResponse(BaseModel):
    diagnosis_id: str
    s3_key: str
    s3_url: str
    width: int
    height: int
    normalized_path: str
    quality: ImageQualityFlags
    passed_quality: bool
    rejection_reason: Optional[str] = None
    processing_ms: int
