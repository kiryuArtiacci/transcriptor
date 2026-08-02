"""Persistencia de configuración de usuario en JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger(__name__)

_DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "Español",
    "backend_whisper": False,
    "identify_speakers": False,
    "geometry": "1000x750",
}


def _config_path() -> Path:
    import platform

    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Local" / "transcriptor"
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "transcriptor"
    else:
        base = (
            Path.home()
            / ".local"
            / "share"
            / "transcriptor"
        )
    base.mkdir(parents=True, exist_ok=True)
    return base / "config.json"


def load_config() -> Dict[str, Any]:
    """Carga la configuración desde disco, con valores por defecto."""
    cfg = dict(_DEFAULT_CONFIG)
    path = _config_path()
    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            cfg.update(saved)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("No se pudo cargar config.json: %s", exc)
    return cfg


def save_config(updates: Dict[str, Any]) -> None:
    """Guarda las claves indicadas en disco, fusionando con lo existente."""
    cfg = load_config()
    cfg.update(updates)
    try:
        _config_path().write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("No se pudo guardar config.json: %s", exc)
