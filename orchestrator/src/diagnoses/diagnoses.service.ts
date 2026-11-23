import {
  Injectable,
  NotFoundException,
  ForbiddenException,
} from '@nestjs/common';
import { v4 as uuidv4 } from 'uuid';
import { basename, join } from 'path';
import { writeFileSync, mkdirSync } from 'fs';
import { DiagnosesStore } from './diagnoses.store';
import { PipelineService } from './pipeline.service';
import { CreateDiagnosisDto } from './dto/create-diagnosis.dto';
import { ValidateDiagnosisDto } from './dto/validate-diagnosis.dto';
import { Diagnosis } from '../shared/interfaces';
import { DiagnosisStatus, UserRole } from '../shared/enums';

const UPLOAD_DIR = process.env.UPLOAD_DIR || './uploads';
mkdirSync(UPLOAD_DIR, { recursive: true });

@Injectable()
export class DiagnosesService {
  constructor(
    private readonly store: DiagnosesStore,
    private readonly pipeline: PipelineService,
  ) {}

  private withImageUrl(d: Diagnosis) {
    const file = d.imagePath ? basename(d.imagePath) : '';
    const imageUrl = file ? `/uploads/${file}` : '';

    let result = d.result;
    if (result?.gradCamUrl) {
      const gcPath = result.gradCamUrl.replace('file://', '');
      const gcFile = basename(gcPath);
      result = { ...result, gradCamUrl: gcFile ? `/gradcam/${gcFile}` : null };
    }

    return { ...d, imageUrl, result };
  }

  async create(
    dto: CreateDiagnosisDto,
    requestUser: any,
  ): Promise<Diagnosis> {
    let imagePath = '';
    if (dto.imageBase64) {
      const buffer = Buffer.from(dto.imageBase64, 'base64');
      const fname = `${uuidv4()}.jpg`;
      imagePath = join(UPLOAD_DIR, fname);
      writeFileSync(imagePath, buffer);
    }

    const diagnosis: Diagnosis = {
      id: `diag_${uuidv4()}`,
      patientId: dto.patientId,
      doctorId: requestUser.role === UserRole.DOCTOR ? requestUser.id : null,
      specializationId: dto.specializationId,
      imageSource: dto.imageSource,
      imagePath,
      symptoms: dto.symptoms || null,
      status: DiagnosisStatus.SUBMITTED,
      pipeline: [
        {
          step: DiagnosisStatus.SUBMITTED,
          startedAt: new Date().toISOString(),
          completedAt: new Date().toISOString(),
          agentId: 'orchestrator',
          error: null,
        },
      ],
      result: null,
      doctorNote: null,
      prescription: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.store.save(diagnosis);

    // Run pipeline asynchronously (fire and forget for MVP)
    this.pipeline.run(diagnosis).catch(() => {});

    return this.withImageUrl(diagnosis);
  }

  findById(id: string) {
    const d = this.store.findById(id);
    if (!d) throw new NotFoundException(`Diagnosis ${id} not found`);
    return this.withImageUrl(d);
  }

  findByPatient(patientId: string) {
    return this.store.findByPatient(patientId).map(d => this.withImageUrl(d));
  }

  findAll() {
    return this.store.findAll().map(d => this.withImageUrl(d));
  }

  validate(id: string, dto: ValidateDiagnosisDto, doctor: any) {
    const d = this.store.findById(id);
    if (!d) throw new NotFoundException(`Diagnosis ${id} not found`);
    if (d.status !== DiagnosisStatus.PENDING_REVIEW) {
      throw new ForbiddenException('Diagnosis is not pending review');
    }

    d.status = dto.status as unknown as DiagnosisStatus;
    d.doctorId = doctor.id;
    d.doctorNote = dto.doctorNote || null;
    d.prescription = dto.prescription || null;
    d.updatedAt = new Date().toISOString();

    if (dto.status === DiagnosisStatus.APPROVED) {
      d.status = DiagnosisStatus.COMPLETED;
    }

    this.store.save(d);
    return this.withImageUrl(d);
  }
}
