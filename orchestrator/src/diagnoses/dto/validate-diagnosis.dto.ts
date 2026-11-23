import { IsEnum, IsOptional, IsString } from 'class-validator';
import { DiagnosisStatus } from '../../shared/enums';

export class ValidateDiagnosisDto {
  @IsEnum(DiagnosisStatus)
  status: DiagnosisStatus.APPROVED | DiagnosisStatus.REJECTED;

  @IsString()
  @IsOptional()
  doctorNote?: string;

  @IsString()
  @IsOptional()
  prescription?: string;
}
