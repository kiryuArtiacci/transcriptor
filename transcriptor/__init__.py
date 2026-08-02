"""Transcriptor — Transcripción de audio a texto con OCR.

Paquete principal.
"""

__version__ = "2.1.0"


def _setup_runtime() -> None:
    """Configura FFmpeg antes que cualquier módulo lo use."""
    import shutil

    from .config import IS_COMPILED, app_dir
    from .utils.logger import get_logger

    logger = get_logger("setup")
    ffmpeg_path = None

    if IS_COMPILED:
        candidate = app_dir() / "ffmpeg.exe"
        if candidate.is_file():
            ffmpeg_path = str(candidate)

    if not ffmpeg_path:
        ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path:
        from pydub import AudioSegment

        AudioSegment.converter = ffmpeg_path
        logger.info("FFmpeg configurado: %s", ffmpeg_path)
    else:
        logger.warning(
            "FFmpeg no encontrado. Convierta archivos a WAV o instale: "
            "winget install Gyan.FFmpeg"
        )


_setup_runtime()
