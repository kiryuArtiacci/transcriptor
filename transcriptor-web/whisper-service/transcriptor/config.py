"""Configuración para el microservicio whisper."""

DIAR_MIN_SEGMENT_MS = 150
DIAR_MIN_SAMPLES = 2400
DIAR_RMS_THRESHOLD = 0.002
DIAR_TIME_GAP_S = 5.0
DIAR_GAP_PENALTY_MAX = 0.35
DIAR_GAP_PENALTY_RATE = 0.02
DIAR_THRESHOLD_FLOOR = 0.45
DIAR_THRESHOLD_CAP = 0.88

WHISPER_MODEL_SIZE = "base"
WHISPER_COMPUTE_TYPE = "int8"
FILE_CHUNK_DURATION = 30

SUPPORTED_AUDIO_EXTENSIONS = [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"]
TESSERACT_SEARCH_PATHS = ["/usr/bin/tesseract"]
TESSDATA_REPO = "https://github.com/tesseract-ocr/tessdata/raw/main"

from pathlib import Path
import sys
import os

BASE_DIR = Path(__file__).resolve().parent.parent
IS_COMPILED = getattr(sys, "frozen", False)


def app_dir() -> Path:
    if IS_COMPILED:
        return Path(sys.executable).resolve().parent
    return BASE_DIR


def resource_path(relative: str) -> Path:
    if IS_COMPILED:
        return Path(sys.executable).resolve().parent / relative
    return BASE_DIR / relative


def whisper_lang(google_code: str) -> str:
    return google_code.split("-")[0]
