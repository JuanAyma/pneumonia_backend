import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { ValidationPipe } from '@nestjs/common';
import * as express from 'express';
import { AppModule } from './app.module';

async function bootstrap() {
  // bodyParser: false lets multer own the multipart stream without interference
  const app = await NestFactory.create<NestExpressApplication>(AppModule, {
    bodyParser: false,
  });

  // Re-add parsers only for JSON / urlencoded — multer handles multipart
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  const uploadDir = process.env.UPLOAD_DIR || './uploads';
  app.useStaticAssets(uploadDir, { prefix: '/uploads' });

  const gradCamDir = process.env.GRADCAM_DIR || '/tmp/pneumonia_images';
  app.useStaticAssets(gradCamDir, { prefix: '/gradcam' });

  app.useGlobalPipes(
    new ValidationPipe({ whitelist: true, transform: true }),
  );

  app.enableCors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  });

  app.setGlobalPrefix('v1');

  const port = process.env.PORT || 3000;
  await app.listen(port);
  console.log(`Orchestrator running on http://localhost:${port}/v1`);
}
bootstrap();
