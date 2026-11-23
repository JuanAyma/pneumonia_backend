import { DiagnosisStatus, RiskLevel, ImageSource, UserRole } from './enums';

export interface User {
  id: string;
  email: string;
  passwordHash: string;
  role: UserRole;
  name: string;
}

export interface PipelineStep {
  step: DiagnosisStatus;
  startedAt: string;
  completedAt: string | null;
  agentId: string;
  error: string | null;
}

export interface Diagnosis {
  id: string;
  patientId: string;
  doctorId: string | null;
  specializationId: string;
  imageSource: ImageSource;
  imagePath: string;
  symptoms: Record<string, unknown> | null;
  status: DiagnosisStatus;
  pipeline: PipelineStep[];
  result: DiagnosisResult | null;
  doctorNote: string | null;
  prescription: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface DiagnosisResult {
  hasPneumonia: boolean;
  confidence: number;
  riskLevel: RiskLevel;
  gradCamUrl: string | null;
  findings: Finding[];
  urgencyHours: number;
  recommendedActions: string[];
  reportUrl: string | null;
}

export interface Finding {
  code: string;
  description: string;
  confidence: number;
  source: string;
}
