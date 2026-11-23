import { Module } from '@nestjs/common';
import { DiagnosesController } from './diagnoses.controller';
import { DiagnosesService } from './diagnoses.service';
import { DiagnosesStore } from './diagnoses.store';
import { PipelineService } from './pipeline.service';

@Module({
  controllers: [DiagnosesController],
  providers: [DiagnosesService, DiagnosesStore, PipelineService],
})
export class DiagnosesModule {}
