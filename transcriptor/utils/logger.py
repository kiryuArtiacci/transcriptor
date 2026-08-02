"""Configuración de logging centralizada."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    log_file: Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configura y devuelve el logger raíz de la aplicación.

    Args:
        log_file: Ruta opcional para guardar logs en archivo.
        level: Nivel de logging (por defecto INFO).

    Returns:
        Logger raíz configurado.
    """
    logger = logging.getLogger("transcriptor")
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre dado, hijo del logger raíz."""
    return logging.getLogger(f"transcriptor.{name}")
