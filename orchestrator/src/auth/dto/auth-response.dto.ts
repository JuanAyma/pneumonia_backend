import { UserRole } from '../../shared/enums';

export class UserDto {
  id: string;
  email: string;
  role: UserRole;
  name: string;
}

export class AuthResponseDto {
  accessToken: string;
  refreshToken: string;
  user: UserDto;
}
