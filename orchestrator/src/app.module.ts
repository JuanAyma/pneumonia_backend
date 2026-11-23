import { Module } from '@nestjs/common';
import { AuthModule } from './auth/auth.module';
import { DiagnosesModule } from './diagnoses/diagnoses.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [AuthModule, DiagnosesModule, UsersModule],
})
export class AppModule {}
