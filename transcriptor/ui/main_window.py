"""Ventana principal de la aplicación Transcriptor."""

from __future__ import annotations

import json
import queue
from datetime import datetime
from pathlib import Path
from typing import Any

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ..config import (
    APP_NAME,
    APP_VERSION,
    LANGUAGES,
    DEFAULT_LANGUAGE,
    UI_WINDOW_TITLE,
    UI_WINDOW_SIZE,
    UI_WINDOW_MINSIZE,
    UI_APPEARANCE_MODE,
    UI_COLOR_THEME,
    EXPORT_FILE_TYPES,
    QUEUE_POLL_INTERVAL_MS,
)
from ..core.transcriber import TranscriptionResult
from ..utils.config_store import load_config, save_config
from ..utils.logger import get_logger
from .widgets import Message
from .recording_tab import RecordingTab
from .file_tab import FileImportTab
from .ocr_tab import OCRTab

logger = get_logger(__name__)


class MainWindow(ctk.CTk):
    """Ventana principal con pestañas de grabación, importación de archivos y OCR."""

    def __init__(self) -> None:
        super().__init__()

        self._message_queue: queue.Queue = queue.Queue()
        self._last_result: Any = None
        self._config = load_config()

        ctk.set_appearance_mode(UI_APPEARANCE_MODE)
        ctk.set_default_color_theme(UI_COLOR_THEME)

        self.title(f"{UI_WINDOW_TITLE} v{APP_VERSION}")
        self.geometry(self._config.get("geometry", UI_WINDOW_SIZE))
        self.minsize(*UI_WINDOW_MINSIZE)

        self._build_ui()
        self._apply_config()
        self._process_messages()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        self._lang_var = ctk.StringVar(value=DEFAULT_LANGUAGE)
        lang_menu = ctk.CTkOptionMenu(
            header,
            values=list(LANGUAGES.keys()),
            variable=self._lang_var,
            command=self._on_language_changed,
            width=120,
        )
        lang_menu.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self._tabview = ctk.CTkTabview(self)
        self._tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self._tab_recording = self._tabview.add("Grabación en Vivo")
        self._tab_file = self._tabview.add("Importar Archivo")
        self._tab_ocr = self._tabview.add("OCR — Imagen")

        self._recording_tab = RecordingTab(
            self._tab_recording, self._message_queue
        )
        self._recording_tab.pack(fill="both", expand=True, padx=5, pady=5)

        self._file_tab = FileImportTab(
            self._tab_file, self._message_queue
        )
        self._file_tab.pack(fill="both", expand=True, padx=5, pady=5)

        self._ocr_tab = OCRTab(
            self._tab_ocr, self._message_queue
        )
        self._ocr_tab.pack(fill="both", expand=True, padx=5, pady=5)

        text_frame = ctk.CTkFrame(self)
        text_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            text_frame,
            text="Transcripción:",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(10, 5))

        self._textbox = ctk.CTkTextbox(
            text_frame, font=ctk.CTkFont(size=14), wrap="word"
        )
        self._textbox.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(status_frame)
        self._progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self._progress_bar.set(0)

        self._status_label = ctk.CTkLabel(
            status_frame,
            text="Listo para comenzar",
            font=ctk.CTkFont(size=12),
        )
        self._status_label.grid(row=1, column=0, pady=(0, 10))

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Limpiar",
            command=self._clear_transcription,
            fg_color="gray",
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Copiar",
            command=self._copy_to_clipboard,
            fg_color="gray",
            width=80,
        ).pack(side="left", padx=5)

        self._save_btn = ctk.CTkButton(
            btn_frame,
            text="Guardar",
            command=self._save_transcription,
            fg_color="green",
        )
        self._save_btn.pack(side="right", padx=5)

        export_types = [ft[0] for ft in EXPORT_FILE_TYPES[:-1]]
        self._export_var = ctk.StringVar(value=export_types[0])
        ctk.CTkOptionMenu(
            btn_frame,
            values=export_types,
            variable=self._export_var,
            width=180,
        ).pack(side="right", padx=5)

        self._bind_shortcuts()

    def _on_language_changed(self, choice: str) -> None:
        lang_codes = LANGUAGES.get(choice, LANGUAGES[DEFAULT_LANGUAGE])
        self._recording_tab.set_language(lang_codes["google"])
        self._file_tab.set_language(lang_codes["google"])
        self._ocr_tab.set_language(lang_codes["tesseract"])
        logger.info("Idioma cambiado a: %s", choice)

    def _process_messages(self) -> None:
        try:
            while True:
                msg: Message = self._message_queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        finally:
            self.after(QUEUE_POLL_INTERVAL_MS, self._process_messages)

    def _handle_message(self, msg: Message) -> None:
        msg_type = msg.type

        if msg_type == "transcription":
            self._textbox.insert("end", msg.payload + " ")
            self._textbox.see("end")

        elif msg_type == "final_transcription":
            if msg.payload.strip():
                self._textbox.insert("end", msg.payload + "\n\n")
                self._textbox.see("end")
                self._set_status("Transcripción completada")
            else:
                self._set_status("No se pudo transcribir el audio")

        elif msg_type == "transcription_result":
            result: TranscriptionResult = msg.payload
            self._last_result = result

            if not result.full_text.strip():
                self._set_status("No se pudo transcribir el audio")
                return

            speakers_present = any(seg.speaker_id > 0 for seg in result.segments)

            if speakers_present and result.segments:
                unique_speakers = sorted(
                    {seg.speaker_id for seg in result.segments if seg.speaker_id}
                )
                header = f"--- Transcripción con {len(unique_speakers)} hablante(s) detectado(s) ---\n"
                segment_lines = []
                for seg in result.segments:
                    speaker_prefix = (
                        f"[Hablante {seg.speaker_id}] "
                        if seg.speaker_id
                        else ""
                    )
                    segment_lines.append(
                        f"[{seg.start:06.2f}s - {seg.end:06.2f}s] "
                        f"{speaker_prefix}{seg.text}"
                    )
                display_text = header + "\n".join(segment_lines) + "\n\n"

            elif result.segments:
                segment_lines = []
                for seg in result.segments:
                    segment_lines.append(
                        f"[{seg.start:06.2f}s - {seg.end:06.2f}s] {seg.text}"
                    )
                display_text = "\n".join(segment_lines) + "\n\n"
            else:
                display_text = result.full_text + "\n\n"

            self._textbox.insert("end", display_text)
            self._textbox.see("end")
            self._set_status(
                f"Transcripción completada ({result.backend}, {result.duration:.1f}s)"
            )

        elif msg_type == "ocr_result":
            self._textbox.insert("end", f"\n--- OCR ---\n{msg.payload}\n\n")
            self._textbox.see("end")

        elif msg_type == "progress":
            self._progress_bar.set(msg.payload)

        elif msg_type == "progress_start":
            self._progress_bar.start()

        elif msg_type == "progress_stop":
            self._progress_bar.stop()
            self._progress_bar.set(0)

        elif msg_type == "transcribe_finished":
            self._set_status("Listo para comenzar")

        elif msg_type == "status":
            self._set_status(msg.payload)

        elif msg_type == "error":
            self._set_status(f"Error: {msg.payload}")
            messagebox.showerror("Error", str(msg.payload))
            self._progress_bar.stop()
            self._progress_bar.set(0)

    def _set_status(self, text: str) -> None:
        self._status_label.configure(text=text)
        self._recording_tab.update_status(text)

    def _clear_transcription(self) -> None:
        self._textbox.delete("1.0", "end")
        self._set_status("Transcripción limpiada")

    def _save_transcription(self) -> None:
        text = self._textbox.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Advertencia", "No hay texto para guardar.")
            return

        export_choice = self._export_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_choice == "Archivo de texto":
            exts = [("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")]
            def_ext = ".txt"
            initial = f"transcripcion_{timestamp}.txt"
            file_path = filedialog.asksaveasfilename(
                defaultextension=def_ext,
                filetypes=exts,
                initialfile=initial,
            )
            if file_path:
                self._write_file(file_path, text)

        elif export_choice == "Subtítulos SRT":
            srt_content = self._generate_srt(text)
            if not srt_content:
                messagebox.showwarning(
                    "Sin segmentos",
                    "La exportación SRT requiere transcripción con timestamps.\n"
                    "Use el motor whisper (offline) o la opción 'Identificar hablantes'.",
                )
                return
            exts = [("Subtítulos", "*.srt"), ("Todos los archivos", "*.*")]
            def_ext = ".srt"
            initial = f"transcripcion_{timestamp}.srt"
            file_path = filedialog.asksaveasfilename(
                defaultextension=def_ext,
                filetypes=exts,
                initialfile=initial,
            )
            if file_path:
                self._write_file(file_path, srt_content)

        elif export_choice == "JSON con segmentos":
            json_content = self._generate_json(text)
            if not json_content:
                messagebox.showwarning(
                    "Sin segmentos",
                    "La exportación JSON requiere transcripción con segmentos.\n"
                    "Use el motor whisper (offline) o la opción 'Identificar hablantes'.",
                )
                return
            exts = [("JSON", "*.json"), ("Todos los archivos", "*.*")]
            def_ext = ".json"
            initial = f"transcripcion_{timestamp}.json"
            file_path = filedialog.asksaveasfilename(
                defaultextension=def_ext,
                filetypes=exts,
                initialfile=initial,
            )
            if file_path:
                self._write_file(file_path, json_content)

    def _generate_srt(self, text: str) -> str:
        if not hasattr(self, "_last_result") or not self._last_result.segments:
            return ""

        from ..core.transcriber import Transcriber

        srt = Transcriber.segments_to_srt(self._last_result.segments)
        return srt

    def _generate_json(self, text: str) -> str:
        if not hasattr(self, "_last_result") or not self._last_result.segments:
            return ""

        segments_data = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": seg.speaker_id,
            }
            for seg in self._last_result.segments
        ]
        return json.dumps(
            {
                "language": self._last_result.language,
                "backend": self._last_result.backend,
                "duration": self._last_result.duration,
                "segments": segments_data,
            },
            indent=2,
            ensure_ascii=False,
        )

    def _write_file(self, file_path: str, content: str) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Éxito", f"Guardado en:\n{file_path}")
            self._set_status("Archivo guardado exitosamente")
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo guardar: {exc}")

    def _apply_config(self) -> None:
        lang = self._config.get("language", DEFAULT_LANGUAGE)
        if lang in LANGUAGES:
            self._lang_var.set(lang)
            self._on_language_changed(lang)

    def _on_close(self) -> None:
        try:
            save_config({
                "language": self._lang_var.get(),
                "geometry": self.geometry(),
            })
        except Exception:
            pass
        self.destroy()

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-l>", lambda _: self._clear_transcription())
        self.bind("<Control-s>", lambda _: self._save_transcription())
        self.bind("<Control-c>", lambda _: self._copy_to_clipboard())

    def _copy_to_clipboard(self) -> None:
        text = self._textbox.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("Texto copiado al portapapeles")
