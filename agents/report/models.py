from pydantic import BaseModel
from typing import Any
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ReportRequest(BaseModel):
    diagnosis_id: str
    patient_id: str
    doctor_id: str
    specialization_id: str
    diagnostic: Any
    symptom_analysis: Any
    correlation: Any

class ReportResponse(BaseModel):
    diagnosis_id: str
    report_s3_key: str
    report_url: str
    notification_sent: bool
    notification_channel: str
    generated_at: str
    page_count: int
