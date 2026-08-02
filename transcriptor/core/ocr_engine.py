"""Motor de OCR para extraer texto de imágenes usando Tesseract.

Incluye descarga automática de datos de idioma faltantes desde
el repositorio oficial de tessdata.
"""

from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Optional

from ..config import TESSERACT_SEARCH_PATHS, TESSDATA_REPO, app_dir, IS_COMPILED
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OCREngine:
    """Motor de reconocimiento óptico de caracteres (OCR) usando Tesseract.

    Attributes:
        tesseract_path: Ruta al ejecutable de Tesseract (opcional).
        available: Indica si Tesseract está instalado y accesible.
    """

    def __init__(self, tesseract_path: str | None = None) -> None:
        self.tesseract_path = tesseract_path
        self.available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Verifica si Tesseract OCR está instalado usando múltiples estrategias.

        Estrategias en orden:
          1. Ruta explícita configurada por el usuario.
          2. Búsqueda en PATH del sistema (shutil.which).
          3. Recorrido de TESSERACT_SEARCH_PATHS.
          4. Detección automática de pytesseract (registro de Windows).

        Returns:
            True si se encontró un Tesseract funcional.
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract no está instalado. OCR deshabilitado.")
            return False

        import pytesseract.pytesseract as pyt_core
        _get_version = pytesseract.get_tesseract_version

        candidates = []

        if self.tesseract_path:
            candidates.append(("ruta configurada", Path(self.tesseract_path)))

        system_tesseract = shutil.which("tesseract")
        if system_tesseract:
            candidates.append(("PATH del sistema", Path(system_tesseract)))

        if IS_COMPILED:
            bundled = app_dir() / "tesseract.exe"
            if bundled.is_file():
                candidates.append(("junto al .exe", bundled))

        for search_path in TESSERACT_SEARCH_PATHS:
            p = Path(search_path)
            if p.is_file() and p not in [c[1] for c in candidates]:
                candidates.append(("directorio predefinido", p))

        for source, t_path in candidates:
            try:
                pyt_core.tesseract_cmd = str(t_path)
                version = _get_version()
                self.tesseract_path = str(t_path)
                logger.info(
                    "Tesseract OCR detectado (%s): %s (v%s)",
                    source,
                    t_path,
                    version,
                )
                return True
            except Exception:
                logger.debug("Falló candidato Tesseract (%s): %s", source, t_path)
                continue

        try:
            version = _get_version()
            self.tesseract_path = pyt_core.tesseract_cmd
            logger.info(
                "Tesseract OCR detectado (auto): %s (v%s)",
                self.tesseract_path,
                version,
            )
            return True
        except Exception as exc:
            logger.warning(
                "Tesseract no encontrado. Instálelo desde: "
                "https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Error: %s",
                exc,
            )
            return False

    def set_tesseract_path(self, path: str) -> bool:
        """Configura manualmente la ruta a tesseract.exe y revalida.

        Args:
            path: Ruta absoluta al ejecutable de Tesseract.

        Returns:
            True si la ruta es válida y Tesseract responde correctamente.
        """
        import pytesseract
        import pytesseract.pytesseract as pyt_core

        t_path = Path(path)
        if not t_path.is_file():
            logger.warning("Ruta de Tesseract no válida: %s", path)
            self.available = False
            return False

        try:
            pyt_core.tesseract_cmd = str(t_path)
            version = pytesseract.get_tesseract_version()
            self.tesseract_path = str(t_path)
            self.available = True
            logger.info(
                "Tesseract configurado manualmente: %s (v%s)",
                t_path,
                version,
            )
            return True
        except Exception as exc:
            logger.warning("Tesseract no responde en la ruta '%s': %s", path, exc)
            self.available = False
            return False

    def _get_app_data_dir(self) -> Path:
        """Directorio de datos de la aplicación, por SO.

        Returns:
            Windows: %LOCALAPPDATA%\\transcriptor
            Linux:   ~/.local/share/transcriptor
            macOS:   ~/Library/Application Support/transcriptor
        """
        if os.name == "nt":
            base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(base) / "transcriptor"
        elif os.uname().sysname == "Darwin":
            return Path.home() / "Library" / "Application Support" / "transcriptor"
        else:
            return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "transcriptor"

    def _get_tessdata_dir(self) -> Path:
        """Obtiene un directorio 'tessdata' con permisos de escritura.

        La carpeta DEBE llamarse exactamente 'tessdata' para que Tesseract
        la encuentre vía TESSDATA_PREFIX.

        Si es nuevo, copia eng.traineddata desde la instalación del sistema.
        Migra archivos desde ~/.tessdata (directorio antiguo) si existen.
        """
        tessdata_dir = self._get_app_data_dir() / "tessdata"

        old_dir = Path.home() / ".tessdata"
        if old_dir.is_dir() and not tessdata_dir.is_dir():
            try:
                shutil.move(str(old_dir), str(tessdata_dir))
                logger.info(
                    "Migrado tessdata: %s -> %s", old_dir, tessdata_dir
                )
            except Exception as exc:
                logger.warning("No se pudo migrar tessdata: %s", exc)
                tessdata_dir.mkdir(parents=True, exist_ok=True)
                for f in old_dir.glob("*.traineddata"):
                    try:
                        shutil.copy2(str(f), str(tessdata_dir / f.name))
                    except Exception:
                        pass
        else:
            tessdata_dir.mkdir(parents=True, exist_ok=True)

        eng_file = tessdata_dir / "eng.traineddata"
        if not eng_file.exists():
            system_tessdata = self._find_system_tessdata()
            if system_tessdata is not None:
                system_eng = system_tessdata / "eng.traineddata"
                if system_eng.exists():
                    try:
                        shutil.copy2(str(system_eng), str(eng_file))
                        logger.info(
                            "eng.traineddata copiado a %s", tessdata_dir
                        )
                    except Exception as exc:
                        logger.warning(
                            "No se pudo copiar eng.traineddata: %s", exc
                        )

        return tessdata_dir

    def _find_system_tessdata(self) -> Path | None:
        """Busca el directorio tessdata de la instalación del sistema."""
        if self.tesseract_path:
            tessdata = Path(self.tesseract_path).parent / "tessdata"
            if tessdata.is_dir():
                return tessdata

        from ..config import TESSERACT_SEARCH_PATHS

        for search_path in TESSERACT_SEARCH_PATHS:
            tessdata = Path(search_path).parent / "tessdata"
            if tessdata.is_dir():
                return tessdata

        return None

    def _download_language_data(self, lang: str, dest_dir: Path) -> bool:
        """Descarga un archivo .traineddata desde el repositorio oficial.

        Args:
            lang: Código de idioma (ej. 'spa', 'eng').
            dest_dir: Directorio donde guardar el archivo.

        Returns:
            True si la descarga fue exitosa.
        """
        url = f"{TESSDATA_REPO}/{lang}.traineddata"
        dest_file = dest_dir / f"{lang}.traineddata"

        logger.info("Descargando datos de idioma '%s'...", lang)

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                dest_file.write_bytes(response.read())
            file_size_kb = dest_file.stat().st_size / 1024

            if file_size_kb < 100:
                dest_file.unlink()
                logger.warning(
                    "Archivo descargado demasiado pequeño (%d KB) — "
                    "probablemente inválido. ¿Existe el idioma '%s'?",
                    int(file_size_kb),
                    lang,
                )
                return False

            logger.info(
                "Datos de idioma '%s' descargados (%d KB).",
                lang,
                int(file_size_kb),
            )
            return True
        except Exception as exc:
            logger.warning("Error al descargar '%s': %s", url, exc)
            if dest_file.exists():
                dest_file.unlink()
            return False

    def _ensure_language(self, language: str) -> str:
        """Asegura que los datos del idioma existen, descargándolos si es necesario.

        Args:
            language: Código de idioma (ej. 'spa', 'eng', 'spa+eng').

        Returns:
            Código de idioma usable. Si el idioma solicitado falla, devuelve 'eng'.
        """
        tessdata_dir = self._get_tessdata_dir()
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

        logger.debug("TESSDATA_PREFIX=%s", tessdata_dir)

        if language in ("eng", "osd"):
            return language

        for sublang in language.split("+"):
            sublang = sublang.strip()
            if sublang in ("eng", "osd"):
                continue

            traineddata = tessdata_dir / f"{sublang}.traineddata"
            if traineddata.exists():
                logger.debug("'%s.traineddata' ya existe.", sublang)
                continue

            logger.info(
                "Falta '%s.traineddata'. Descargando a %s...",
                sublang,
                tessdata_dir,
            )
            success = self._download_language_data(sublang, tessdata_dir)
            if not success:
                logger.warning(
                    "No se pudo descargar '%s'. Usando 'eng' como fallback.",
                    sublang,
                )
                return "eng"

        return language

    def extract_text(
        self,
        image_path: str | Path,
        language: str = "spa",
    ) -> Optional[str]:
        """Extrae texto de una imagen usando OCR.

        Descarga automáticamente los datos de idioma si faltan en tessdata.

        Args:
            image_path: Ruta a la imagen (PNG, JPG, TIFF, BMP, PDF).
            language: Código de idioma Tesseract (ej. 'spa', 'eng', 'spa+eng').

        Returns:
            Texto extraído, o None si el OCR no está disponible o falla.

        Raises:
            FileNotFoundError: Si el archivo de imagen no existe.
        """
        if not self.available:
            logger.error("OCR no disponible. Instale Tesseract OCR.")
            return None

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

        import pytesseract
        from PIL import Image

        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        resolved_language = self._ensure_language(language)
        logger.info(
            "Procesando OCR en '%s' (idioma: %s)...",
            image_path.name,
            resolved_language,
        )

        try:
            suffix = image_path.suffix.lower()
            if suffix == ".pdf":
                text = self._extract_from_pdf(str(image_path), resolved_language)
            else:
                image = Image.open(str(image_path))
                text = pytesseract.image_to_string(image, lang=resolved_language)

            result = text.strip() if text else None
            if result:
                logger.info("OCR completado: %d caracteres.", len(result))
            else:
                logger.info("OCR no encontró texto en la imagen.")
            return result

        except pytesseract.TesseractError as exc:
            logger.error("Error de Tesseract: %s", exc)
            return None
        except Exception as exc:
            logger.exception("Error inesperado en OCR: %s", exc)
            return None

    def _extract_from_pdf(self, pdf_path: str, language: str) -> str:
        """Extrae texto de la primera página de un PDF usando OCR."""
        try:
            from pdf2image import convert_from_path
        except ImportError:
            logger.warning(
                "pdf2image no instalado. Ejecute: pip install pdf2image"
            )
            return ""

        import pytesseract

        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if not images:
            return ""

        resolved = self._ensure_language(language)
        return pytesseract.image_to_string(images[0], lang=resolved)

    def get_available_languages(self) -> list[str]:
        """Obtiene la lista de idiomas disponibles (sistema + usuario).

        Returns:
            Lista de códigos de idioma instalados.
        """
        if not self.available:
            return []

        try:
            import pytesseract

            if self.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        except Exception:
            return []

        langs: set[str] = set()

        try:
            langs.update(pytesseract.get_languages())
        except Exception:
            pass

        tessdata_dir = self._get_tessdata_dir()
        if tessdata_dir.is_dir():
            for f in tessdata_dir.glob("*.traineddata"):
                langs.add(f.stem)

        return sorted(langs)
