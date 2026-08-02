"""Pestaña de OCR para extraer texto de imágenes."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from typing import Any, Optional

import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog

from ..config import SUPPORTED_IMAGE_EXTENSIONS, DEFAULT_LANGUAGE_OCR, LANGUAGES, DEFAULT_LANGUAGE
from ..core.ocr_engine import OCREngine
from ..utils.logger import get_logger
from .widgets import Message

logger = get_logger(__name__)

IMAGE_PREVIEW_SIZE = (400, 300)


class OCRTab(ctk.CTkFrame):
    """Pestaña para cargar imágenes y extraer texto con OCR (Tesseract)."""

    def __init__(
        self,
        master: Any,
        message_queue: queue.Queue,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._message_queue = message_queue
        self._ocr = OCREngine()
        self._selected_file: Optional[str] = None
        self._ocr_language = DEFAULT_LANGUAGE_OCR

        self._build_ui()
        self._refresh_ocr_status()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self._status_display = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=14),
        )
        self._status_display.pack(pady=10)

        self._tesseract_actions_frame = ctk.CTkFrame(frame)
        self._tesseract_actions_frame.pack(pady=5)

        self._browse_tesseract_btn = ctk.CTkButton(
            self._tesseract_actions_frame,
            text="📁 Buscar tesseract.exe",
            command=self._browse_tesseract,
            width=200,
            height=30,
            fg_color="orange",
        )

        self._install_info = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._install_info.pack(pady=5)

        self._import_btn = ctk.CTkButton(
            frame,
            text="🖼️ Cargar Imagen",
            command=self._import_image,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16),
        )
        self._import_btn.pack(pady=20)

        self._file_info = ctk.CTkLabel(
            frame,
            text="Formatos: PNG, JPG, JPEG, TIFF, BMP, PDF",
            font=ctk.CTkFont(size=12),
        )
        self._file_info.pack(pady=5)

        self._ocr_lang_var = ctk.StringVar(value="spa")
        self._ocr_lang_menu = ctk.CTkOptionMenu(
            frame,
            values=["spa", "eng"],
            variable=self._ocr_lang_var,
            command=self._on_ocr_lang_changed,
            width=120,
        )
        self._ocr_lang_menu.pack(pady=5)

        self._lang_info = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._lang_info.pack(pady=2)

        self._preview_label = ctk.CTkLabel(frame, text="")
        self._preview_label.pack(pady=10)

        self._extract_btn = ctk.CTkButton(
            frame,
            text="🔍 Extraer Texto",
            command=self._extract_text,
            state="disabled",
            width=200,
            height=40,
        )
        self._extract_btn.pack(pady=10)

    def _refresh_ocr_status(self) -> None:
        if self._ocr.available:
            self._status_display.configure(
                text="Tesseract disponible",
                text_color="green",
            )
            self._browse_tesseract_btn.pack_forget()
            self._install_info.configure(text="")
            self._refresh_language_dropdown()
        else:
            self._status_display.configure(
                text="Tesseract no detectado",
                text_color="red",
            )
            self._browse_tesseract_btn.pack(pady=5)
            self._install_info.configure(
                text=(
                    "Instale Tesseract OCR o busque el ejecutable manualmente.\n"
                    "Descargar: https://github.com/UB-Mannheim/tesseract/wiki"
                ),
            )
            self._lang_info.configure(text="")

    def _refresh_language_dropdown(self) -> None:
        installed = self._ocr.get_available_languages()
        if not installed:
            return

        tesseract_map = {
            v["tesseract"]: k
            for k, v in LANGUAGES.items()
        }
        display_values = [
            tesseract_map.get(code, code) for code in installed
        ]
        self._ocr_lang_menu.configure(values=display_values)

        if display_values:
            current_display = tesseract_map.get(self._ocr_language, self._ocr_language)
            if current_display in display_values:
                self._ocr_lang_var.set(current_display)
            else:
                self._ocr_lang_var.set(display_values[0])
                self._ocr_language = installed[0]

        missing = [
            tesseract_map.get(lang, lang)
            for lang in tesseract_map
            if lang not in installed and lang != "eng"
        ]
        if missing:
            self._lang_info.configure(
                text=f"Idiomas descargables: {', '.join(missing)}",
                text_color="orange",
            )
        else:
            self._lang_info.configure(text="")

    def _on_ocr_lang_changed(self, display_name: str) -> None:
        for name, codes in LANGUAGES.items():
            if name == display_name:
                self._ocr_language = codes["tesseract"]
                return
        self._ocr_language = display_name

    def _browse_tesseract(self) -> None:
        import platform

        is_windows = platform.system() == "Windows"
        exe_pattern = "tesseract.exe" if is_windows else "tesseract"
        file_path = filedialog.askopenfilename(
            title="Seleccionar tesseract",
            filetypes=[
                ("Tesseract ejecutable", exe_pattern),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not file_path:
            return

        success = self._ocr.set_tesseract_path(file_path)
        if success:
            self._message_queue.put(
                Message("status", "Tesseract configurado correctamente.")
            )
        else:
            self._message_queue.put(
                Message("error", f"No se pudo usar Tesseract en:\n{file_path}")
            )

        self._refresh_ocr_status()

    def _import_image(self) -> None:
        ext_pattern = " ".join(f"*{ext}" for ext in SUPPORTED_IMAGE_EXTENSIONS)
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", ext_pattern),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not file_path:
            return

        suffix = Path(file_path).suffix.lower()
        if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
            self._message_queue.put(
                Message("error", "Formato de imagen no soportado.")
            )
            return

        self._selected_file = file_path
        self._file_info.configure(
            text=f"Imagen: {os.path.basename(file_path)}"
        )
        self._extract_btn.configure(state="normal")
        self._show_preview(file_path)

    def _show_preview(self, file_path: str) -> None:
        if Path(file_path).suffix.lower() == ".pdf":
            self._preview_label.configure(
                text="(Vista previa no disponible para PDF)"
            )
            return

        try:
            img = Image.open(file_path)
            img.thumbnail(IMAGE_PREVIEW_SIZE, Image.LANCZOS)
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size,
            )
            self._preview_label.configure(image=ctk_img, text="")
            self._preview_label.image = ctk_img
        except Exception as exc:
            logger.warning("No se pudo mostrar vista previa: %s", exc)
            self._preview_label.configure(text="")

    def _extract_text(self) -> None:
        if not self._selected_file:
            self._message_queue.put(
                Message("error", "Seleccione una imagen primero.")
            )
            return

        if not self._ocr.available:
            self._message_queue.put(
                Message("error", "Tesseract OCR no está instalado o configurado.")
            )
            return

        self._extract_btn.configure(state="disabled")
        self._import_btn.configure(state="disabled")
        self._message_queue.put(Message("status", "Extrayendo texto de la imagen..."))

        threading.Thread(target=self._run_ocr, daemon=True).start()

    def _run_ocr(self) -> None:
        try:
            text = self._ocr.extract_text(
                self._selected_file,
                language=self._ocr_language,
            )

            if text:
                self._message_queue.put(Message("ocr_result", text))
                self._message_queue.put(
                    Message("status", "Texto extraído correctamente")
                )
            else:
                self._message_queue.put(
                    Message("status", "No se encontró texto en la imagen")
                )
        except FileNotFoundError as exc:
            self._message_queue.put(Message("error", str(exc)))
        except Exception as exc:
            logger.exception("Error en OCR: %s", exc)
            self._message_queue.put(Message("error", f"Error en OCR: {exc}"))
        finally:
            self._import_btn.configure(state="normal")
            self._extract_btn.configure(state="normal")

    def set_language(self, tesseract_code: str) -> None:
        self._ocr_language = tesseract_code
        for name, codes in LANGUAGES.items():
            if codes["tesseract"] == tesseract_code:
                self._ocr_lang_var.set(name)
                return
