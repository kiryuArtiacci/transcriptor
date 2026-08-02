# Transcriptor Web v2.1.0

Aplicación web de transcripción de audio a texto con diarización de hablantes y OCR.

## Requisitos previos

| Herramienta | Versión | Instalación |
|------------|---------|-------------|
| Docker Desktop | 29+ | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Git | Cualquiera | `winget install Git.Git` |
| Java 21 + Maven 3.9+ | Solo para desarrollo | `winget install Oracle.JDK.21` + [maven.apache.org](https://maven.apache.org) |

## Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/kiryuArtiacci/transcriptor.git
cd transcriptor/transcriptor-web

# 2. Compilar backend
cd backend
mvn package -DskipTests
cd ..

# 3. Levantar servicios
docker compose up -d

# 4. Abrir en navegador
# http://localhost:3000
```

## Servicios

| Servicio | Puerto | Tecnología | Rol |
|----------|--------|-----------|-----|
| **frontend** | 3000 | React 18 + TypeScript + Nginx | Interfaz de usuario |
| **backend** | 8080 | Spring Boot 3.3 + Java 21 + Tess4J | API REST + WebSocket + OCR |
| **whisper** | 5000 (interno) | Python Flask + faster-whisper | Transcripción y diarización |

## Funcionalidades

| Funcionalidad | Estado | Requisito |
|---------------|:---:|-----------|
| Grabación en vivo (micrófono) | ✅ | Permiso de micrófono en navegador |
| Importar archivo → transcribir (Whisper) | ✅ | ~2 GB RAM disponible |
| Diarización de hablantes | ✅ | Checkbox "Identificar hablantes" |
| OCR de imágenes (Tesseract) | ✅ | Imagen PNG/JPG/TIFF/BMP |
| Exportar TXT, SRT, JSON | ✅ | — |
| 6 idiomas (ES, EN, FR, DE, PT, IT) | ✅ | — |

## Detener

```bash
docker compose down
```

## Ver logs

```bash
docker compose logs -f whisper   # Transcripción
docker compose logs -f backend   # API
docker compose logs -f frontend  # Web
```

## Tamaños de imagen Docker

| Imagen | Tamaño |
|--------|--------|
| transcriptor-frontend:2.1.0 | ~50 MB |
| transcriptor-backend:2.1.0 | ~350 MB |
| transcriptor-whisper:2.1.0 | ~2 GB |

## Primera ejecución

El modelo whisper base (~140 MB) se descarga automáticamente del Hub de HuggingFace.
Requiere conexión a internet. Ejecuciones siguientes usan el modelo cacheado
(volumen `whisper_cache`).

## Desarrollo sin Docker

```bash
# Whisper service
cd whisper-service
python -m venv venv && venv\Scripts\activate   # Windows
# source venv/bin/activate                      # Linux/macOS
pip install -r requirements.txt
python app.py                                    # → localhost:5000

# Backend (requiere Java 21 + Maven)
cd backend
mvn spring-boot:run                              # → localhost:8080

# Frontend
cd frontend
npm install && npm run dev                       # → localhost:3000
```

## Solución de problemas

### `port is already allocated`

```bash
# Liberar puerto 3000 en Windows
Get-NetTCPConnection -LocalPort 3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Luego reiniciar
docker compose down && docker compose up -d
```

### Whisper service no arranca

```bash
docker compose logs whisper
# Si ves "faster-whisper not found", espera — la primera build descarga dependencias
```

### Backend no compila

Java 21 debe estar en PATH:
```bash
java --version   # Debe mostrar 21.x
mvn --version    # Debe mostrar 3.9+
```

## Arquitectura

```
Navegador (React + TS) → http://localhost:3000
       │
       ▼ REST + WebSocket
Spring Boot (Java 21) → http://localhost:8080
       │
       ▼ HTTP (red interna Docker)
Flask (Python) → http://whisper:5000
       │
       ▼
faster-whisper + diarización MFCC
```

## Estructura del proyecto

```
transcriptor-web/
├── docker-compose.yml
├── README.md
├── frontend/              # React + TypeScript (Vite + Nginx)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── components/    # RecordingTab, FileImportTab, OcrTab, etc.
│       ├── hooks/         # useAudioRecorder
│       └── services/      # api.ts (cliente axios)
├── backend/               # Spring Boot 3.3 (Java 21 + Maven)
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/main/java/com/transcriptor/
│       ├── controller/    # REST + WebSocket
│       ├── service/       # WhisperClient, TranscriptionService, OcrService
│       ├── model/         # DTOs
│       └── config/        # CORS, WebSocket
└── whisper-service/       # Python Flask + faster-whisper
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py             # API REST (POST /transcribe)
    └── transcriptor/      # Motor de transcripción y diarización
        └── core/
            ├── transcriber.py
            └── audio_processor.py
```
