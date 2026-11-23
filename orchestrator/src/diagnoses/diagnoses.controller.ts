import {
  Body,
  Controller,
  Get,
  Param,
  Post,
  Req,
  UseGuards,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { DiagnosesService } from './diagnoses.service';
import { CreateDiagnosisDto } from './dto/create-diagnosis.dto';
import { ValidateDiagnosisDto } from './dto/validate-diagnosis.dto';

@Controller()
@UseGuards(JwtAuthGuard)
export class DiagnosesController {
  constructor(private readonly service: DiagnosesService) {}

  @Post('diagnoses')
  async create(@Body() dto: CreateDiagnosisDto, @Req() req: any) {
    console.log('[DIAG] create() entered — imageBase64:', dto.imageBase64 ? `${dto.imageBase64.length} chars` : 'missing');
    const diagnosis = await this.service.create(dto, req.user);
    console.log('[DIAG] returning 201 for', diagnosis.id);
    return diagnosis;
  }

  @Get('diagnoses')
  findAll() {
    return this.service.findAll();
  }

  @Get('diagnoses/:id')
  findOne(@Param('id') id: string) {
    return this.service.findById(id);
  }

  @Post('diagnoses/:id/validate')
  validate(
    @Param('id') id: string,
    @Body() dto: ValidateDiagnosisDto,
    @Req() req: any,
  ) {
    return this.service.validate(id, dto, req.user);
  }

  @Get('patients/:patientId/diagnoses')
  findByPatient(@Param('patientId') patientId: string) {
    return this.service.findByPatient(patientId);
  }
}
