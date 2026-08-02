# Transcriptor v2.0.0

Aplicación de escritorio para transcripción de audio a texto y OCR de imágenes.

## Características

- **Grabación en vivo**: Transcribe audio del micrófono en tiempo real (Google STT).
- **Importar archivos**: Transcribe archivos WAV, MP3, OGG, FLAC, M4A, AAC.
- **Motor offline**: Usa [faster-whisper](https://github.com/SYSTRAN/faster-whisper) para transcripción offline con timestamps.
- **Diarización de hablantes**: Identifica distintas voces en el audio usando [resemblyzer](https://github.com/resemble-ai/Resemblyzer). Detecta automáticamente cuántas personas hablan y etiqueta cada segmento (`[Hablante 1]`, `[Hablante 2]`, etc.).
- **OCR de imágenes**: Extrae texto de PNG, JPG, TIFF, BMP y PDF usando Tesseract.
- **Múltiples idiomas**: Español, English, Français, Deutsch, Português, Italiano, 日本語, 中文.
- **Exportación**: TXT, SRT (subtítulos) y JSON (con segmentos y timestamps).

## Requisitos

| Requisito | Versión |
|-----------|---------|
| Python | 3.10 o superior |
| pip | 24.0+ |

### Dependencias externas del sistema

**FFmpeg** (requerido para procesar audio):
```powershell
# Windows (winget)
winget install ffmpeg

# O descargar manualmente de https://ffmpeg.org/download.html
```

**Tesseract OCR** (requerido para extraer texto de imágenes):
```powershell
# Windows (winget)
winget install tesseract-ocr

# O descargar de https://github.com/UB-Mannheim/tesseract/wiki
```

**Poppler** (requerido para OCR de PDFs — opcional):
```powershell
# Descargar de https://github.com/oschwartz10612/poppler-windows/releases
# Agregar la carpeta bin/ al PATH del sistema
```

## Instalación

```powershell
# 1. Clonar o entrar al directorio del proyecto
cd transcriptor

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

### Notas para Windows

- `PyAudio` puede fallar al instalar desde pip. Si ocurre, instalar la rueda precompilada:
  ```powershell
  pip install pipwin
  pipwin install pyaudio
  ```
- Asegúrate de que `ffmpeg` y `tesseract` estén en el `PATH` del sistema.
- Para whisper offline, la primera ejecución descargará el modelo (~140MB para `base`).

### Notas para Linux/macOS

```bash
# Ubuntu/Debian
sudo apt install ffmpeg tesseract-ocr tesseract-ocr-spa poppler-utils portaudio19-dev

# macOS
brew install ffmpeg tesseract tesseract-lang poppler portaudio

# Luego
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Uso

1. **Grabación en Vivo**: Selecciona el idioma, presiona "Iniciar Grabación" y habla.
2. **Importar Archivo**: Carga un audio y elige entre Google STT (online) o whisper (offline).
3. **OCR — Imagen**: Carga una imagen y extrae el texto.
4. **Guardar**: Elige el formato de exportación (TXT, SRT, JSON) y guarda.

## Estructura del proyecto

```
transcriptor/
├── app.py                    # Entry point
├── requirements.txt
├── README.md
└── transcriptor/             # Paquete principal
    ├── __init__.py
    ├── app.py                # Inicialización
    ├── config.py             # Configuración centralizada
    ├── core/
    │   ├── audio_processor.py  # Conversión y chunking de audio
    │   ├── recorder.py         # Grabación en vivo
    │   ├── transcriber.py      # Motores STT (Google + whisper)
    │   └── ocr_engine.py       # Motor OCR (Tesseract)
    ├── ui/
    │   ├── main_window.py      # Ventana principal
    │   ├── recording_tab.py    # Pestaña de grabación
    │   ├── file_tab.py         # Pestaña de importar archivos
    │   ├── ocr_tab.py          # Pestaña de OCR
    │   └── widgets.py          # Componentes reutilizables
    └── utils/
        └── logger.py           # Configuración de logging
```

## Licencia

Uso personal y educativo.
