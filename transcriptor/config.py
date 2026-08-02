"""Configuración centralizada de la aplicación."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

APP_NAME = "Transcriptor"
APP_VERSION = "2.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent
IS_COMPILED = getattr(sys, "frozen", False)


def app_dir() -> Path:
    """Directorio raíz: proyecto en desarrollo, exe en compilado."""
    if IS_COMPILED:
        return Path(sys.executable).resolve().parent
    return BASE_DIR


def resource_path(relative: str) -> Path:
    """Resuelve ruta a un recurso, tanto en dev como en .exe compilado."""
    if IS_COMPILED:
        return Path(sys.executable).resolve().parent / relative
    return BASE_DIR / relative

LANGUAGES: Dict[str, Dict[str, str]] = {
    "Español":    {"google": "es-ES", "whisper": "es",  "tesseract": "spa"},
    "English":    {"google": "en-US", "whisper": "en",  "tesseract": "eng"},
    "Français":   {"google": "fr-FR", "whisper": "fr",  "tesseract": "fra"},
    "Deutsch":    {"google": "de-DE", "whisper": "de",  "tesseract": "deu"},
    "Português":  {"google": "pt-BR", "whisper": "pt",  "tesseract": "por"},
    "Italiano":   {"google": "it-IT", "whisper": "it",  "tesseract": "ita"},
    "日本語":       {"google": "ja-JP", "whisper": "ja",  "tesseract": "jpn"},
    "中文":        {"google": "zh-CN", "whisper": "zh",  "tesseract": "chi_sim"},
}

DEFAULT_LANGUAGE = "Español"
DEFAULT_LANGUAGE_OCR = "spa"


def whisper_lang(google_code: str) -> str:
    """Convierte código Google (es-ES) a código whisper (es)."""
    return google_code.split("-")[0]


_WHISPER_SIZES = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
WHISPER_MODEL_SIZE = "base"
WHISPER_COMPUTE_TYPE = "int8"

RECORDING_ENERGY_THRESHOLD = 300
RECORDING_PAUSE_THRESHOLD = 0.8
RECORDING_PHRASE_TIME_LIMIT = 5
RECORDING_AMBIENT_ADJUST_DURATION = 1
RECORDING_POLL_INTERVAL = 0.05

FILE_CHUNK_DURATION = 30

SUPPORTED_AUDIO_EXTENSIONS: List[str] = [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"]
SUPPORTED_IMAGE_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".pdf"]

TESSERACT_SEARCH_PATHS: List[str] = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]

TESSDATA_REPO = "https://github.com/tesseract-ocr/tessdata/raw/main"

DIAR_MIN_SEGMENT_MS = 150
DIAR_MIN_SAMPLES = 2400
DIAR_RMS_THRESHOLD = 0.002
DIAR_TIME_GAP_S = 5.0
DIAR_GAP_PENALTY_MAX = 0.35
DIAR_GAP_PENALTY_RATE = 0.02
DIAR_THRESHOLD_FLOOR = 0.45
DIAR_THRESHOLD_CAP = 0.88

UI_WINDOW_TITLE = f"{APP_NAME} — Transcripción de Audio y OCR"
UI_WINDOW_SIZE = "1000x750"
UI_WINDOW_MINSIZE = (900, 650)
UI_APPEARANCE_MODE = "dark"
UI_COLOR_THEME = "blue"

EXPORT_FILE_TYPES: List[Tuple[str, str]] = [
    ("Archivo de texto", "*.txt"),
    ("Subtítulos SRT", "*.srt"),
    ("JSON con segmentos", "*.json"),
    ("Todos los archivos", "*.*"),
]

QUEUE_POLL_INTERVAL_MS = 100
