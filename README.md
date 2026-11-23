# Sistema de Diagnóstico de Neumonía — Backend

Backend del sistema móvil multiplataforma para detección temprana de neumonía mediante Deep Learning.  
Tesis UNMSM 2026 — Ayma Pumainca Juan Fidel

---

## Arquitectura general

El backend está compuesto por un **orquestador NestJS** (único punto de entrada público) que coordina cinco **microagentes FastAPI** especializados, cada uno ejecutándose en su propio contenedor Docker.

```
Flutter App
    │
    ▼ HTTP (puerto 3000)
┌─────────────────────────────┐
│   Orquestador NestJS        │
│   JWT Auth · REST API       │
│   Pipeline secuencial       │
└──────┬──────────────────────┘
       │ HTTP interno
       ├──▶ image-agent      :8001  Ingesta y normalización de imagen
       ├──▶ diagnostic-agent :8002  Inferencia TFLite + Grad-CAM (Keras)
       ├──▶ symptom-agent    :8003  Análisis de síntomas clínicos
       ├──▶ correlation-agent:8004  Correlación diagnóstico + síntomas
       └──▶ report-agent     :8005  Generación de reporte final
```

---

## Requisitos previos

- **Docker Desktop 4.16.3** con Docker Compose v2
- Node.js 20+ (solo si se ejecuta el orquestador fuera de Docker)
- Python 3.11+ (solo si se ejecuta un agente fuera de Docker)
- Archivos de modelo en `agents/diagnostic/models/` (ver sección Modelos de IA)

> **Nota sobre versión de Docker Desktop:** Las versiones posteriores a la 4.16.x cambiaron el backend de red interno (de VPNKit a un nuevo proxy), lo que bloquea bodies HTTP grandes entre el host y los contenedores. Se recomienda usar la versión **4.16.3** para desarrollo local en Windows. En Linux/AWS no hay restricción de versión.

---

## Modelos de IA

El `diagnostic-agent` usa dos archivos de modelo, ambos deben estar en `agents/diagnostic/models/`:

| Archivo | Uso | Obligatorio |
|---|---|---|
| `resnet50_etapa2_rsna.tflite` | Inferencia (clasificación) | No — hay mock por brillo |
| `resnet50_etapa2_rsna.keras` | Grad-CAM (mapa de atención) | No — hay simulación Gaussiana |

Si falta alguno, el agente usa un fallback automático y el pipeline sigue funcionando.

**Umbral de clasificación:** `confidence > 0.5` → PNEUMONIA

**Niveles de riesgo:**

| Confianza | Riesgo |
|---|---|
| ≤ 0.50 | LOW |
| 0.50 – 0.60 | MODERATE |
| 0.60 – 0.85 | HIGH |
| > 0.85 | CRITICAL |

### Grad-CAM

El agente genera un mapa de atención PNG superpuesto sobre la radiografía original y lo sirve en `GET /gradcam/{id}_gradcam.png`.

- **Con `.keras`:** Grad-CAM real via `tf.GradientTape` sobre la última capa convolucional (`conv5_block3_out`). El heatmap es específico a cada imagen.
- **Sin `.keras`:** Simulación con Gaussianas centradas en los lóbulos inferiores (patrón anatómico típico de neumonía).

Los archivos PNG se guardan en el volumen Docker `images` (`/tmp/pneumonia_images/`), compartido entre `diagnostic-agent` y el orquestador.

---

## Levantar el sistema completo

```bash
# Desde el directorio Backend/
docker-compose up --build        # primera vez o tras cambios en el código
docker-compose up                # ejecuciones siguientes
docker-compose down              # detener y eliminar contenedores
```

Para reconstruir solo un servicio:

```bash
docker-compose up --build diagnostic-agent
```

---

## Puertos y variables de entorno

| Servicio | Puerto | Variable de entorno en el orquestador |
|---|---|---|
| Orquestador | 3000 | — |
| image-agent | 8001 | `IMAGE_AGENT_URL` |
| diagnostic-agent | 8002 | `DIAGNOSTIC_AGENT_URL` |
| symptom-agent | 8003 | `SYMPTOM_AGENT_URL` |
| correlation-agent | 8004 | `CORRELATION_AGENT_URL` |
| report-agent | 8005 | `REPORT_AGENT_URL` |

Las variables tienen como valor por defecto `http://localhost:800x` para desarrollo fuera de Docker.

**Variables obligatorias a sobreescribir en producción:**

| Variable | Por defecto | Descripción |
|---|---|---|
| `JWT_SECRET` | `dev_secret_change_in_prod` | Clave de firma JWT |
| `UPLOAD_DIR` | `./uploads` | Directorio de imágenes subidas |
| `MODEL_DIR` | `""` | Ruta a los modelos del diagnostic-agent |

---

## API del orquestador

Todas las rutas requieren `Authorization: Bearer <token>` excepto el login.

### Autenticación

```
POST /v1/auth/login
Body: { "email": "...", "password": "..." }
Respuesta: { "accessToken": "...", "user": { "id", "role", "name" } }
```

Credenciales de desarrollo:
- Doctor: `doctor@hospital.com` / `doctor123`
- Paciente: `juan.perez@salud.pe` / `1234`

### Diagnósticos

```
POST   /v1/diagnoses                        Crear diagnóstico (JSON con imageBase64)
GET    /v1/diagnoses/:id                    Consultar estado y resultado
POST   /v1/diagnoses/:id/validate           Validar (solo rol DOCTOR)
GET    /v1/patients/:patientId/diagnoses    Historial de un paciente
GET    /gradcam/:filename                   Imagen Grad-CAM generada por diagnostic-agent
```

**Body de creación (`POST /v1/diagnoses`):**
```json
{
  "patientId": "p001",
  "specializationId": "pulmonology",
  "imageSource": "PATIENT_UPLOAD",
  "symptoms": { "fever": 38.5, "cough": true },
  "imageBase64": "<imagen codificada en base64>"
}
```

**Campos relevantes de la respuesta (`result`):**
```json
{
  "hasPneumonia": true,
  "confidence": 0.69,
  "riskLevel": "HIGH",
  "gradCamUrl": "/gradcam/diag_abc123_gradcam.png",
  "findings": [...],
  "urgencyHours": 24,
  "recommendedActions": [...]
}
```

---

## Flujo del pipeline

Cuando se sube una radiografía, el orquestador lanza el pipeline en segundo plano y devuelve el diagnóstico en estado `SUBMITTED`. El cliente hace polling a `GET /v1/diagnoses/:id` para seguir el progreso.

```
SUBMITTED
   → QUALITY_CHECK    (image-agent verifica calidad)
   → ANALYZING        (diagnostic-agent: inferencia TFLite + Grad-CAM Keras)
   → CORRELATING      (symptom-agent + correlation-agent + report-agent)
   → PENDING_REVIEW   (esperando validación del médico)
   → APPROVED / COMPLETED  (médico validó el diagnóstico)
      o
   → REJECTED         (médico rechazó el diagnóstico)
```

El resultado no es visible para el paciente hasta que el médico valide.

---

## Persistencia

> ⚠️ El orquestador utiliza almacenamiento **en memoria** (`DiagnosesStore`). Todos los datos se pierden al reiniciar. Para producción debe reemplazarse por PostgreSQL u otro motor de base de datos persistente.

---

## Solución de problemas

### ECONNRESET al subir imágenes (Docker Desktop > 4.16.x en Windows)

Las versiones recientes de Docker Desktop cambiaron su proxy de red interno, bloqueando bodies HTTP grandes. Si actualizas Docker Desktop y el pipeline falla con `read ECONNRESET`, tienes tres opciones:

1. **Recomendado:** Volver a Docker Desktop **4.16.3** (instala y desactiva actualizaciones automáticas)
2. Activar `Features in development → Enable host networking` y agregar `network_mode: host` al orquestador en `docker-compose.yml` (beta, incierto)
3. Ejecutar el orquestador fuera de Docker con `npm run start:dev` y los agentes en Docker

### Error `Exec format error` en bcrypt al hacer `docker-compose up --build`

Ocurre cuando `npm install` se ejecutó en Windows antes de levantar Docker, copiando binarios nativos de Windows al contenedor Linux. El archivo `orchestrator/.dockerignore` ya excluye `node_modules` para evitarlo. Si persiste, elimina la carpeta `orchestrator/node_modules/` antes de hacer el build.

---

## Agregar un nuevo agente

1. Crear el directorio `agents/<nombre>/` con `main.py`, `service.py`, `models.py`, `requirements.txt` y `Dockerfile`.
2. Agregar el servicio en `docker-compose.yml` con su puerto y variables de entorno.
3. Agregar la variable `<NOMBRE>_AGENT_URL` en el servicio `orchestrator` del `docker-compose.yml`.
4. Leer la URL en `PipelineService` y agregar el paso correspondiente en el método `run()`.

---

## Estructura del proyecto

```
Backend/
├── docker-compose.yml
├── orchestrator/              NestJS — orquestador central
│   └── src/
│       ├── auth/              Login, JWT strategy, guard
│       ├── diagnoses/         CRUD, pipeline, store en memoria
│       ├── users/             Gestión de usuarios
│       └── shared/            Interfaces, enums (Diagnosis, UserRole, etc.)
└── agents/                    Microagentes FastAPI (Python)
    ├── image_ingestion/       :8001
    ├── diagnostic/            :8002
    │   └── models/            resnet50_etapa2_rsna.tflite + .keras
    ├── symptom_analysis/      :8003
    ├── correlation/           :8004
    └── report/                :8005
```
