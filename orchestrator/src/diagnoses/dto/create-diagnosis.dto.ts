import { IsEnum, IsObject, IsOptional, IsString } from 'class-validator';
import { Transform } from 'class-transformer';
import { ImageSource } from '../../shared/enums';

export class CreateDiagnosisDto {
  @IsString()
  patientId: string;

  @IsString()
  specializationId: string;

  @IsEnum(ImageSource)
  imageSource: ImageSource;

  @IsString()
  @IsOptional()
  imageBase64?: string;

  @IsObject()
  @IsOptional()
  @Transform(({ value }) => {
    if (typeof value === 'string') {
      try { return JSON.parse(value); } catch { return {}; }
    }
    return value ?? {};
  })
  symptoms?: Record<string, unknown>;
}
