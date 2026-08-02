# Transcriptor Web v2.1.0

Aplicación web de transcripción de audio a texto con diarización de hablantes y OCR.

## Requisitos

- Docker y Docker Compose

## Inicio rápido

```bash
docker compose up -d
```

Abrir en el navegador: **http://localhost:3000**

## Servicios

| Servicio | Puerto | Tecnología |
|----------|--------|-----------|
| Frontend | 3000 | React + TypeScript + Nginx |
| Backend | 8080 | Spring Boot 3.3 + Java 21 |
| Whisper | 5000 (interno) | Python Flask + faster-whisper |

## Funcionalidades

- **Grabación en vivo**: Transcribe desde el micrófono del navegador
- **Importar archivo**: Sube y transcribe archivos WAV, MP3, OGG, FLAC, M4A, AAC
- **Diarización**: Identifica hablantes distintos (requiere whisper)
- **OCR**: Extrae texto de imágenes (PNG, JPG, TIFF, BMP)
- **Exportación**: TXT, SRT, JSON con segmentos y hablantes
- **Idiomas**: Español, English, Français, Deutsch, Português, Italiano

## Detener

```bash
docker compose down
```

## Primera ejecución

El modelo whisper base (~140 MB) se descarga automáticamente en el primer uso.
Requiere conexión a internet. Las ejecuciones siguientes usan el modelo cacheado.

## Desarrollo

```bash
# Whisper service (Python)
cd whisper-service && pip install -r requirements.txt && python app.py

# Backend (Java + Maven)
cd backend && mvn spring-boot:run

# Frontend (React)
cd frontend && npm install && npm run dev
```

## Estructura

```
transcriptor-web/
├── docker-compose.yml
├── frontend/          # React + TypeScript (Vite)
├── backend/           # Spring Boot 3.3 (Java 21)
└── whisper-service/   # Python Flask + faster-whisper
```
