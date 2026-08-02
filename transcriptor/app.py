"""Transcriptor — Aplicación de transcripción de audio y OCR.

Entry point principal de la aplicación.
"""

from __future__ import annotations

from pathlib import Path

from .utils.logger import setup_logging, get_logger


def main() -> None:
    """Inicializa el logging y lanza la interfaz gráfica."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    setup_logging(
        log_file=log_dir / "transcriptor.log",
    )
    logger = get_logger("app")
    logger.info("Iniciando Transcriptor v2.0.0...")

    from .ui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
