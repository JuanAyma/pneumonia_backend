import { Injectable } from '@nestjs/common';
import { Diagnosis } from '../shared/interfaces';

@Injectable()
export class DiagnosesStore {
  private diagnoses: Map<string, Diagnosis> = new Map();

  save(diagnosis: Diagnosis): Diagnosis {
    this.diagnoses.set(diagnosis.id, diagnosis);
    return diagnosis;
  }

  findById(id: string): Diagnosis | undefined {
    return this.diagnoses.get(id);
  }

  findByPatient(patientId: string): Diagnosis[] {
    return Array.from(this.diagnoses.values()).filter(d => d.patientId === patientId);
  }

  findAll(): Diagnosis[] {
    return Array.from(this.diagnoses.values());
  }
}
