from enum import Enum

class DiagnosisStatus(str, Enum):
    SUBMITTED      = 'SUBMITTED'
    QUALITY_CHECK  = 'QUALITY_CHECK'
    ANALYZING      = 'ANALYZING'
    CORRELATING    = 'CORRELATING'
    PENDING_REVIEW = 'PENDING_REVIEW'
    APPROVED       = 'APPROVED'
    REJECTED       = 'REJECTED'
    COMPLETED      = 'COMPLETED'

class RiskLevel(str, Enum):
    LOW      = 'LOW'
    MODERATE = 'MODERATE'
    HIGH     = 'HIGH'
    CRITICAL = 'CRITICAL'

class ImageSource(str, Enum):
    PATIENT_UPLOAD = 'PATIENT_UPLOAD'
    DOCTOR_UPLOAD  = 'DOCTOR_UPLOAD'
