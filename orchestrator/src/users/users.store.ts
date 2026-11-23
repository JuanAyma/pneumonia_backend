import { Injectable } from '@nestjs/common';
import { User } from '../shared/interfaces';
import * as bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { UserRole } from '../shared/enums';

@Injectable()
export class UsersStore {
  private users: Map<string, User> = new Map();

  constructor() {
    // seed default accounts for development
    this.seedDefaultUsers();
  }

  private async seedDefaultUsers() {
    const doctorHash = await bcrypt.hash('doctor123', 10);
    const patientHash = await bcrypt.hash('1234', 10);

    const doctor: User = {
      id: 'user_doctor_001',
      email: 'doctor@hospital.com',
      passwordHash: doctorHash,
      role: UserRole.DOCTOR,
      name: 'Dr. García',
    };

    const patients: User[] = [
      { id: 'p001', email: 'juan.perez@salud.pe',    passwordHash: patientHash, role: UserRole.PATIENT, name: 'Juan Pérez Torres' },
      { id: 'p002', email: 'maria.lopez@salud.pe',   passwordHash: patientHash, role: UserRole.PATIENT, name: 'María López Ramos' },
      { id: 'p003', email: 'carlos.quispe@salud.pe', passwordHash: patientHash, role: UserRole.PATIENT, name: 'Carlos Quispe Huanca' },
    ];

    this.users.set(doctor.id, doctor);
    patients.forEach(p => this.users.set(p.id, p));
  }

  findById(id: string): User | undefined {
    return this.users.get(id);
  }

  findByEmail(email: string): User | undefined {
    return Array.from(this.users.values()).find(u => u.email === email);
  }

  create(user: User): User {
    this.users.set(user.id, user);
    return user;
  }

  findAll(): User[] {
    return Array.from(this.users.values());
  }

  findByRole(role: UserRole): User[] {
    return Array.from(this.users.values()).filter(u => u.role === role);
  }
}
