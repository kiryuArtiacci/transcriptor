"""Procesamiento y conversión de archivos de audio."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from ..config import SUPPORTED_AUDIO_EXTENSIONS, FILE_CHUNK_DURATION
from ..utils.logger import get_logger

logger = get_logger(__name__)

TEMP_PREFIX = "transcriptor_"


def is_audio_file(file_path: str | Path) -> bool:
    """Verifica si un archivo tiene extensión de audio soportada."""
    return Path(file_path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def convert_to_wav(file_path: str | Path) -> str:
    """Convierte un archivo de audio a WAV temporal.

    Args:
        file_path: Ruta al archivo de audio de entrada.

    Returns:
        Ruta al archivo WAV temporal generado.

    Raises:
        FileNotFoundError: Si el archivo de entrada no existe.
        RuntimeError: Si la conversión falla.
    """
    from pydub import AudioSegment

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    logger.info("Convirtiendo '%s' a WAV...", file_path.name)

    try:
        audio = AudioSegment.from_file(str(file_path))
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo abrir '{file_path.name}'. "
            f"Verifique que FFmpeg esté instalado.\n{exc}"
        ) from exc

    temp_fd, temp_wav = tempfile.mkstemp(
        suffix=".wav",
        prefix=TEMP_PREFIX,
    )
    os.close(temp_fd)

    try:
        audio.export(temp_wav, format="wav")
        logger.info("Convertido a WAV: %s", temp_wav)
        return temp_wav
    except Exception as exc:
        _cleanup_temp(temp_wav)
        raise RuntimeError(
            f"Error al exportar '{file_path.name}' a WAV: {exc}"
        ) from exc


def get_audio_duration(file_path: str | Path) -> float:
    """Obtiene la duración de un archivo de audio en segundos.

    Args:
        file_path: Ruta al archivo de audio.

    Returns:
        Duración en segundos, o 0 si no se pudo determinar.
    """
    from pydub import AudioSegment

    try:
        audio = AudioSegment.from_file(str(file_path))
        return audio.duration_seconds
    except Exception:
        logger.warning("No se pudo determinar la duración de '%s'", file_path)
        return 0.0


def get_chunk_count(file_path: str | Path, chunk_duration: int | None = None) -> int:
    """Calcula el número de fragmentos de un archivo de audio.

    Args:
        file_path: Ruta al archivo de audio.
        chunk_duration: Duración de cada fragmento en segundos.

    Returns:
        Número de fragmentos (mínimo 1).
    """
    if chunk_duration is None:
        chunk_duration = FILE_CHUNK_DURATION

    duration = get_audio_duration(file_path)
    return max(1, int(duration / chunk_duration) + (1 if duration % chunk_duration > 0 else 0))


def cleanup_temp_wav(temp_path: str | Path) -> None:
    """Elimina un archivo WAV temporal si existe."""
    _cleanup_temp(temp_path)


def _cleanup_temp(path: str | Path) -> None:
    """Elimina un archivo temporal de forma segura."""
    try:
        if os.path.exists(str(path)):
            os.remove(str(path))
            logger.debug("Archivo temporal eliminado: %s", path)
    except OSError as exc:
        logger.warning("No se pudo eliminar el archivo temporal '%s': %s", path, exc)
