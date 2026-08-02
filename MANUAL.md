# Transcriptor v2.1.0 — Manual de Usuario

Aplicación de escritorio para transcripción de audio a texto con OCR de imágenes
y diarización de hablantes.

---

## 1. Descripción general

Transcriptor es una herramienta de escritorio que convierte voz en texto. Soporta
tres modos de trabajo, accesibles desde las pestañas de la interfaz:

| Pestaña | Función |
|---------|---------|
| **Grabación en Vivo** | Captura audio del micrófono y lo transcribe en tiempo real |
| **Importar Archivo** | Transcribe archivos de audio pregrabados (WAV, MP3, OGG, FLAC, M4A, AAC) |
| **OCR — Imagen** | Extrae texto de imágenes (PNG, JPG, TIFF, BMP, PDF) |

### Idiomas soportados

Español, English, Français, Deutsch, Português, Italiano, 日本語, 中文.

### Motores de transcripción

| Motor | Modo | Internet | Precisión | Timestamps | Diarización |
|-------|------|:---:|:---:|:---:|:---:|
| Google Speech Recognition | Online | ✅ | Media | ❌ | ❌ |
| faster-whisper (base) | Offline | Solo 1ª descarga | Alta | ✅ | ✅ |

---

## 2. Requisitos del sistema

### 2.1 Python y librerías

| Librería | Versión | Rol |
|----------|---------|-----|
| Python | 3.10 o superior | Runtime |
| customtkinter | 5.2.2 | Interfaz gráfica (temas oscuro/claro) |
| SpeechRecognition | 3.16.0 | API de Google Speech-to-Text |
| faster-whisper | 1.1.1 | Transcripción offline con segmentos temporales |
| pydub | 0.25.1 | Manipulación y conversión de formatos de audio |
| PyAudio | 0.2.14 | Captura de audio desde el micrófono |
| Pillow | 10.3.0 | Carga y preview de imágenes |
| pytesseract | 0.3.13 | Interfaz Python para Tesseract OCR |
| pdf2image | 1.17.0 | Conversión de PDF a imagen (OCR de PDFs) |
| numpy | ≥1.26.0, <2.0.0 | Cálculo numérico (FFT, MFCC, álgebra lineal) |
| ctranslate2 | ≥4.0.0, <5.0.0 | Motor de inferencia para faster-whisper |
| huggingface-hub | ≥0.20.0 | Descarga automática del modelo whisper |
| resemblyzer | 0.1.3 *(opcional)* | Diarización premium por embeddings neuronales |
| webrtcvad-wheels | *(opcional)* | Requerido por resemblyzer en Windows |

### 2.2 Programas externos del sistema

| Programa | Windows | Linux (APT) | macOS (Homebrew) | Para qué |
|----------|---------|-------------|-------------------|----------|
| FFmpeg | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` | `brew install ffmpeg` | Conversión de formatos de audio |
| Tesseract OCR | `winget install UB-Mannheim.TesseractOCR` | `sudo apt install tesseract-ocr tesseract-ocr-spa` | `brew install tesseract tesseract-lang` | OCR de imágenes |
| Poppler | [Descargar](https://github.com/oschwartz10612/poppler-windows/releases) | `sudo apt install poppler-utils` | `brew install poppler` | OCR de PDFs *(opcional)* |

### 2.3 Modelo whisper

El modelo `base` (~140 MB) se descarga automáticamente de HuggingFace la primera
vez que se usa el motor whisper. Requiere conexión a internet solo esa primera vez.

---

## 3. Instalación

### 3.1 Método rápido (script automático)

```powershell
python install.py
```

### 3.2 Método manual

```powershell
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Instalar dependencias del sistema
#    Windows:
winget install Gyan.FFmpeg UB-Mannheim.TesseractOCR

#    Linux:
sudo apt install ffmpeg tesseract-ocr tesseract-ocr-spa poppler-utils portaudio19-dev

#    macOS:
brew install ffmpeg tesseract tesseract-lang poppler portaudio

# 4. Ejecutar
python app.py
```

### 3.3 Versión compilada (.exe)

Si tienes la carpeta `dist\Transcriptor\`, no necesitas instalar nada.
Simplemente haz doble clic en `Transcriptor.exe`.

```powershell
# Opcional: copiar binarios junto al .exe para máxima portabilidad
copy "C:\ruta\a\ffmpeg.exe"   "dist\Transcriptor\"
copy "C:\ruta\a\tesseract.exe" "dist\Transcriptor\"
```

### 3.4 Solución de problemas de instalación

**PyAudio falla en Windows:**
```powershell
pip install pipwin
pipwin install pyaudio
```

**Tesseract no se detecta:**
Usa el botón naranja **📁 Buscar tesseract.exe** en la pestaña OCR para
seleccionar manualmente el ejecutable.

---

## 4. Uso de la aplicación

### 4.1 Pestaña "Grabación en Vivo"

1. Verifica que el indicador de micrófono esté en **verde**
2. Selecciona el idioma en el menú superior derecho
3. Opcional: activa **🔊 Identificar hablantes al finalizar**
4. Pulsa **▶ Iniciar Grabación**
5. Habla — el texto aparece en tiempo real (vista previa con Google STT)
6. Usa **⏸ Pausar** / **▶ Reanudar** si necesitas interrumpir
7. Pulsa **⏹ Finalizar** cuando termines

**Con diarización activada**, al finalizar la grabación:
- El audio se exporta a WAV temporal
- Whisper transcribe con timestamps precisos
- El diarizador asigna `[Hablante 1]`, `[Hablante 2]`, etc.
- El resultado con hablantes reemplaza al preview

### 4.2 Pestaña "Importar Archivo"

1. Pulsa **📁 Importar Archivo de Audio**
2. Elige entre:
   - **Google STT** (rápido, requiere internet)
   - **Whisper offline** (más preciso, genera timestamps)
3. Opcional: activa **🔊 Identificar hablantes** (fuerza whisper automáticamente)
4. Pulsa **Transcribir**
5. El resultado aparece en el área de transcripción

### 4.3 Pestaña "OCR — Imagen"

1. Pulsa **🖼️ Cargar Imagen**
2. Selecciona el idioma del texto en la imagen
3. Pulsa **🔍 Extraer Texto**
4. El texto extraído se añade al área de transcripción

**Si Tesseract no se detecta**, aparecerá un botón naranja para buscarlo
manualmente. Los datos de idioma que falten se descargan automáticamente
de internet (~5-20 MB por idioma).

---

## 5. Diarización de hablantes

La diarización permite identificar **quién dijo qué** en una conversación.

### Cómo funciona

1. Whisper divide el audio en segmentos con timestamps
2. Para cada segmento se extraen características de voz (MFCC: coeficientes
   cepstrales en escala Mel, más ZCR, RMS, centroide y planitud espectral)
3. Los segmentos se agrupan por similitud de voz usando clustering
   por unión-búsqueda con umbral adaptativo (percentil 75)
4. Cada grupo recibe una etiqueta: `Hablante 1`, `Hablante 2`, etc.

### Requisitos

- Usar el motor **whisper** (no Google STT)
- Activar el checkbox **🔊 Identificar hablantes**
- Mínimo 2 intervenciones de hablantes distintos

### Motor premium (opcional)

Si instalas `resemblyzer`, el diarizador usa redes neuronales para extraer
embeddings de voz de calidad profesional:

```powershell
pip install webrtcvad-wheels resemblyzer
```

Sin resemblyzer, el sistema usa un extractor basado en numpy (MFCC + pitch)
que funciona sin dependencias adicionales.

---

## 6. Exportación

El panel inferior permite guardar la transcripción en tres formatos:

| Formato | ¿Cuándo disponible? | Contenido |
|---------|---------------------|-----------|
| **TXT** | Siempre | Texto plano |
| **SRT** | Solo con whisper | Subtítulos con timestamps y hablantes |
| **JSON** | Solo con whisper | Segmentos con metadatos (tiempo, hablante, texto) |

### Ejemplo de salida JSON

```json
{
  "language": "es",
  "backend": "whisper-base",
  "duration": 19.7,
  "segments": [
    { "start": 0.5,  "end": 3.2,  "text": "Hola, ¿cómo estás?",    "speaker": 1 },
    { "start": 4.1,  "end": 6.8,  "text": "Muy bien, gracias.",    "speaker": 2 },
    { "start": 7.3,  "end": 9.6,  "text": "¿En qué te ayudo?",     "speaker": 1 }
  ]
}
```

### Ejemplo de salida SRT

```
1
00:00:00,500 --> 00:00:03,200
[Hablante 1] Hola, ¿cómo estás?

2
00:00:04,100 --> 00:00:06,800
[Hablante 2] Muy bien, gracias.
```

### Atajos de teclado

| Tecla | Acción |
|-------|--------|
| Ctrl + C | Copiar transcripción al portapapeles |
| Ctrl + S | Guardar transcripción |
| Ctrl + L | Limpiar área de transcripción |

---

## 7. Arquitectura del proyecto

```
transcriptor/
├── app.py                    # Entry point (4 líneas)
├── install.py                # Instalador multiplataforma
├── requirements.txt          # Dependencias Python pineadas
├── README.md
├── MANUAL.md                 # Este documento
├── Transcriptor.spec         # Spec de PyInstaller
└── transcriptor/             # Paquete principal
    ├── __init__.py           # Configuración de runtime (FFmpeg en .exe)
    ├── app.py                # Inicialización de logging
    ├── config.py             # Constantes, idiomas, paths, umbrales
    ├── core/
    │   ├── audio_processor.py  # Conversión WAV, chunking, FFmpeg
    │   ├── recorder.py         # Grabación de micrófono en vivo
    │   ├── transcriber.py      # Motores STT + diarización + SRT
    │   └── ocr_engine.py       # Tesseract OCR + descarga de idiomas
    ├── ui/
    │   ├── main_window.py      # Ventana principal, mensajes, export
    │   ├── recording_tab.py    # Pestaña de grabación en vivo
    │   ├── file_tab.py         # Pestaña de importar archivos
    │   ├── ocr_tab.py          # Pestaña de OCR con preview
    │   └── widgets.py          # Message (cola), TimerLabel
    └── utils/
        ├── logger.py           # Logging a consola + archivo
        └── config_store.py     # Persistencia de preferencias (JSON)
```

### Flujo de datos

```
Micrófono ──→ AudioRecorder ──→ Google STT (preview en vivo)
                                   │
Archivo ──→ AudioProcessor ──→ Transcriber ──→ UI (texto)
              (WAV/MP3/OGG)      ├─ Google STT
                                 └─ Whisper ──→ Diarizer ──→ UI (hablantes)
                                                  (MFCC+P75)

Imagen ──→ OCREngine ──→ Tesseract ──→ UI (texto)
              (PNG/JPG/PDF)
```

---

## 8. Solución de problemas

### PyAudio no instala en Windows

```powershell
pip install pipwin
pipwin install pyaudio
```

### Tesseract no detectado

- Instálalo con `winget install UB-Mannheim.TesseractOCR`
- O usa el botón **📁 Buscar tesseract.exe** en la pestaña OCR
- La app busca en: `C:\Program Files\Tesseract-OCR\`, `%LOCALAPPDATA%\`, PATH

### Los datos de idioma OCR faltan

La app los descarga automáticamente de GitHub (~5-20 MB por idioma).
Si falla, descárgalos manualmente:

1. Ve a https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata
2. Guarda el archivo en `%LOCALAPPDATA%\transcriptor\tessdata\`

### No se detectan hablantes distintos

1. Asegúrate de que el checkbox **🔊 Identificar hablantes** esté activado
2. Usa el motor **whisper** (no Google STT)
3. Verifica en los logs: `Iniciando diarización con N segmentos`
4. Si dice `Solo 1 segmento — diarización omitida`, el audio es muy corto o
   tiene habla continua sin pausas
5. Graba al menos 10-15 segundos con pausas entre intervenciones

### FFmpeg no encontrado (modo desarrollo)

```powershell
winget install Gyan.FFmpeg
# Reinicia la terminal para que se actualice el PATH
```

### El modelo whisper no se descarga

- Verifica tu conexión a internet
- La primera descarga requiere ~140 MB libres
- Crea un token gratuito en https://huggingface.co/settings/tokens
  y configúralo: `set HF_TOKEN=tu_token`

### El .exe compilado no arranca

- Asegúrate de que `ffmpeg.exe` y `tesseract.exe` estén en la misma
  carpeta que `Transcriptor.exe`
- La carpeta `tessdata/` debe estar junto al `.exe`
- No renombres ni muevas la carpeta `_internal/`

---

## 9. Licencia

Uso personal y educativo. Las librerías de terceros mantienen sus
propias licencias (MIT, Apache 2.0, BSD).
