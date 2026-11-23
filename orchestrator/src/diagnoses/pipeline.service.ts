import { Injectable, Logger } from '@nestjs/common';
import axios from 'axios';
import * as fs from 'fs';
import * as FormData from 'form-data';
import { Diagnosis, PipelineStep } from '../shared/interfaces';
import { DiagnosisStatus, RiskLevel } from '../shared/enums';
import { DiagnosesStore } from './diagnoses.store';

@Injectable()
export class PipelineService {
  private readonly logger = new Logger(PipelineService.name);

  private readonly IMAGE_AGENT   = process.env.IMAGE_AGENT_URL   || 'http://localhost:8001';
  private readonly DIAG_AGENT    = process.env.DIAGNOSTIC_AGENT_URL || 'http://localhost:8002';
  private readonly SYMPTOM_AGENT = process.env.SYMPTOM_AGENT_URL || 'http://localhost:8003';
  private readonly CORR_AGENT    = process.env.CORRELATION_AGENT_URL || 'http://localhost:8004';
  private readonly REPORT_AGENT  = process.env.REPORT_AGENT_URL  || 'http://localhost:8005';

  constructor(private readonly store: DiagnosesStore) {}

  async run(diagnosis: Diagnosis): Promise<void> {
    try {
      // Step 1 — Image Ingestion
      this.setStatus(diagnosis, DiagnosisStatus.QUALITY_CHECK);
      const ingestion = await this.callImageAgent(diagnosis);
      if (!ingestion.passed_quality) {
        this.addStep(diagnosis, DiagnosisStatus.QUALITY_CHECK, 'image-agent', null);
        this.setStatus(diagnosis, DiagnosisStatus.REJECTED);
        this.store.save(diagnosis);
        return;
      }
      this.addStep(diagnosis, DiagnosisStatus.QUALITY_CHECK, 'image-agent', null);

      // Step 2 — Diagnostic
      this.setStatus(diagnosis, DiagnosisStatus.ANALYZING);
      const diagnostic = await this.callDiagnosticAgent(diagnosis, ingestion);
      this.addStep(diagnosis, DiagnosisStatus.ANALYZING, 'diagnostic-agent', null);

      // Step 3 — Symptom Analysis
      this.setStatus(diagnosis, DiagnosisStatus.CORRELATING);
      const symptomResult = await this.callSymptomAgent(diagnosis, diagnostic);
      this.addStep(diagnosis, DiagnosisStatus.CORRELATING, 'symptom-agent', null);

      // Step 4 — Correlation
      const correlation = await this.callCorrelationAgent(diagnosis, diagnostic, symptomResult);
      this.addStep(diagnosis, DiagnosisStatus.CORRELATING, 'correlation-agent', null);

      // Step 5 — Report
      const report = await this.callReportAgent(diagnosis, diagnostic, symptomResult, correlation);
      this.addStep(diagnosis, DiagnosisStatus.CORRELATING, 'report-agent', null);

      // Consolidate result
      diagnosis.result = {
        hasPneumonia: diagnostic.has_pathology,
        confidence: diagnostic.prediction.confidence,
        riskLevel: correlation.final_risk,
        gradCamUrl: diagnostic.grad_cam?.heatmap_url || null,
        findings: correlation.findings || [],
        urgencyHours: correlation.urgency_hours,
        recommendedActions: correlation.recommended_actions || [],
        reportUrl: report.report_url || null,
      };

      this.setStatus(diagnosis, DiagnosisStatus.PENDING_REVIEW);
      this.store.save(diagnosis);
    } catch (err) {
      this.logger.error(`Pipeline failed for ${diagnosis.id}: ${err.message}`);
      this.addStep(diagnosis, diagnosis.status as DiagnosisStatus, 'pipeline', err.message);
      this.setStatus(diagnosis, DiagnosisStatus.REJECTED);
      this.store.save(diagnosis);
    }
  }

  private setStatus(diagnosis: Diagnosis, status: DiagnosisStatus) {
    diagnosis.status = status;
    diagnosis.updatedAt = new Date().toISOString();
    this.store.save(diagnosis);
  }

  private addStep(diagnosis: Diagnosis, step: DiagnosisStatus, agentId: string, error: string | null) {
    const last = diagnosis.pipeline[diagnosis.pipeline.length - 1];
    if (last && !last.completedAt) {
      last.completedAt = new Date().toISOString();
      last.error = error;
    }
    diagnosis.pipeline.push({
      step,
      startedAt: new Date().toISOString(),
      completedAt: null,
      agentId,
      error: null,
    });
  }

  private async callImageAgent(diagnosis: Diagnosis) {
    const imageData = fs.readFileSync(diagnosis.imagePath);
    const b64 = imageData.toString('base64');
    const { data } = await axios.post(`${this.IMAGE_AGENT}/ingest`, {
      diagnosis_id: diagnosis.id,
      image_base64: b64,
      source: diagnosis.imageSource,
      patient_id: diagnosis.patientId,
      specialization_id: diagnosis.specializationId,
    }, { timeout: 30000 });
    return data;
  }

  private async callDiagnosticAgent(diagnosis: Diagnosis, ingestion: any) {
    const { data } = await axios.post(`${this.DIAG_AGENT}/diagnose`, {
      diagnosis_id: diagnosis.id,
      s3_key: ingestion.s3_key,
      normalized_path: ingestion.normalized_path,
      specialization_id: diagnosis.specializationId,
      model_version: 'latest',
    }, { timeout: 60000 });
    return data;
  }

  private async callSymptomAgent(diagnosis: Diagnosis, diagnostic: any) {
    const { data } = await axios.post(`${this.SYMPTOM_AGENT}/analyze`, {
      diagnosis_id: diagnosis.id,
      specialization_id: diagnosis.specializationId,
      symptoms: diagnosis.symptoms || {},
      has_pathology: diagnostic.has_pathology,
      risk_level: diagnostic.risk_level,
    }, { timeout: 15000 });
    return data;
  }

  private async callCorrelationAgent(diagnosis: Diagnosis, diagnostic: any, symptom: any) {
    const { data } = await axios.post(`${this.CORR_AGENT}/correlate`, {
      diagnosis_id: diagnosis.id,
      specialization_id: diagnosis.specializationId,
      diagnostic,
      symptom_analysis: symptom,
    }, { timeout: 15000 });
    return data;
  }

  private async callReportAgent(diagnosis: Diagnosis, diagnostic: any, symptom: any, correlation: any) {
    const { data } = await axios.post(`${this.REPORT_AGENT}/report`, {
      diagnosis_id: diagnosis.id,
      patient_id: diagnosis.patientId,
      doctor_id: diagnosis.doctorId || 'unassigned',
      specialization_id: diagnosis.specializationId,
      diagnostic,
      symptom_analysis: symptom,
      correlation,
    }, { timeout: 30000 });
    return data;
  }
}
