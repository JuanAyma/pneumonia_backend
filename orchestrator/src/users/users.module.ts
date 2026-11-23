import { Module } from '@nestjs/common';
import { UsersStore } from './users.store';

@Module({
  providers: [UsersStore],
  exports: [UsersStore],
})
export class UsersModule {}
