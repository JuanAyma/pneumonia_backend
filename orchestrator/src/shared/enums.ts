export enum DiagnosisStatus {
  SUBMITTED       = 'SUBMITTED',
  QUALITY_CHECK   = 'QUALITY_CHECK',
  ANALYZING       = 'ANALYZING',
  CORRELATING     = 'CORRELATING',
  PENDING_REVIEW  = 'PENDING_REVIEW',
  APPROVED        = 'APPROVED',
  REJECTED        = 'REJECTED',
  COMPLETED       = 'COMPLETED',
}

export enum RiskLevel {
  LOW      = 'LOW',
  MODERATE = 'MODERATE',
  HIGH     = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export enum ImageSource {
  PATIENT_UPLOAD = 'PATIENT_UPLOAD',
  DOCTOR_UPLOAD  = 'DOCTOR_UPLOAD',
}

export enum UserRole {
  DOCTOR  = 'DOCTOR',
  PATIENT = 'PATIENT',
}
