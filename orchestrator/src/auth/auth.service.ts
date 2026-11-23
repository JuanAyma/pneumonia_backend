import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { UsersStore } from '../users/users.store';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { AuthResponseDto } from './dto/auth-response.dto';

@Injectable()
export class AuthService {
  constructor(
    private readonly jwtService: JwtService,
    private readonly usersStore: UsersStore,
  ) {}

  async register(dto: RegisterDto): Promise<AuthResponseDto> {
    const existing = this.usersStore.findByEmail(dto.email);
    if (existing) throw new ConflictException('Email already registered');

    const passwordHash = await bcrypt.hash(dto.password, 10);
    const user = this.usersStore.create({
      id: uuidv4(),
      email: dto.email,
      passwordHash,
      role: dto.role,
      name: dto.name,
    });

    return this.buildTokens(user);
  }

  async login(dto: LoginDto): Promise<AuthResponseDto> {
    const user = this.usersStore.findByEmail(dto.email);
    if (!user) throw new UnauthorizedException('Invalid credentials');

    const valid = await bcrypt.compare(dto.password, user.passwordHash);
    if (!valid) throw new UnauthorizedException('Invalid credentials');

    return this.buildTokens(user);
  }

  private buildTokens(user: any): AuthResponseDto {
    const payload = { sub: user.id, email: user.email, role: user.role };
    return {
      accessToken: this.jwtService.sign(payload, {
        expiresIn: process.env.JWT_EXPIRES_IN || '1h',
      }),
      refreshToken: this.jwtService.sign(payload, {
        expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
      }),
      user: { id: user.id, email: user.email, role: user.role, name: user.name },
    };
  }

  refresh(token: string): AuthResponseDto {
    try {
      const payload = this.jwtService.verify(token);
      const user = this.usersStore.findById(payload.sub);
      if (!user) throw new UnauthorizedException();
      return this.buildTokens(user);
    } catch {
      throw new UnauthorizedException('Invalid refresh token');
    }
  }
}
