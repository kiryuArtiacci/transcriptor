"""Pestaña de importación y transcripción de archivos de audio."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from typing import Any, Optional

import customtkinter as ctk
from tkinter import filedialog

from ..config import whisper_lang
from ..core.audio_processor import is_audio_file
from ..core.transcriber import Transcriber, TranscriptionResult
from ..utils.logger import get_logger
from .widgets import Message

logger = get_logger(__name__)


class FileImportTab(ctk.CTkFrame):
    """Pestaña para importar archivos de audio y transcribirlos."""

    def __init__(
        self,
        master: Any,
        message_queue: queue.Queue,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._message_queue = message_queue
        self._selected_file: Optional[str] = None
        self._transcriber = Transcriber()
        self._use_whisper = False
        self._identify_speakers = False
        self._language = "es-ES"

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self._backend_switch = ctk.CTkSwitch(
            frame,
            text="Usar whisper (offline, más preciso)",
            command=self._toggle_backend,
        )
        self._backend_switch.pack(pady=10, anchor="w", padx=20)

        self._speaker_switch = ctk.CTkSwitch(
            frame,
            text="🔊 Identificar hablantes (diarización)",
            command=self._toggle_speakers,
        )
        self._speaker_switch.pack(pady=5, anchor="w", padx=20)

        self._speaker_note = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._speaker_note.pack(pady=2, anchor="w", padx=20)

        self._import_btn = ctk.CTkButton(
            frame,
            text="📁 Importar Archivo de Audio",
            command=self._import_file,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16),
        )
        self._import_btn.pack(pady=20)

        self._file_info = ctk.CTkLabel(
            frame,
            text="Formatos soportados: WAV, MP3, OGG, FLAC, M4A, AAC",
            font=ctk.CTkFont(size=12),
        )
        self._file_info.pack(pady=5)

        self._progress = ctk.CTkProgressBar(frame)
        self._progress.pack(pady=20, padx=20, fill="x")
        self._progress.set(0)

        self._transcribe_btn = ctk.CTkButton(
            frame,
            text="🎙️ Transcribir Archivo",
            command=self._transcribe_file,
            state="disabled",
            width=200,
            height=40,
        )
        self._transcribe_btn.pack(pady=10)

    def _toggle_backend(self) -> None:
        self._use_whisper = self._backend_switch.get() == 1
        self._update_button_text()

    def _toggle_speakers(self) -> None:
        self._identify_speakers = self._speaker_switch.get() == 1
        if self._identify_speakers:
            self._backend_switch.select()
            self._use_whisper = True
            self._speaker_note.configure(
                text="La diarización requiere whisper. Se ha activado automáticamente.",
                text_color="orange",
            )
        else:
            self._speaker_note.configure(text="")
        self._update_button_text()

    def _update_button_text(self) -> None:
        if self._identify_speakers:
            self._transcribe_btn.configure(
                text="🎙️ Transcribir con identificación de hablantes"
            )
        elif self._use_whisper:
            self._transcribe_btn.configure(text="🎙️ Transcribir (whisper offline)")
        else:
            self._transcribe_btn.configure(text="🎙️ Transcribir (Google STT)")

    def _import_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[
                ("Archivos de audio", "*.wav *.mp3 *.ogg *.flac *.m4a *.aac"),
                ("Archivos WAV", "*.wav"),
                ("Archivos MP3", "*.mp3"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not file_path:
            return

        if not is_audio_file(file_path):
            self._message_queue.put(
                Message("error", "Formato de archivo no soportado.")
            )
            return

        self._selected_file = file_path
        self._file_info.configure(
            text=f"Archivo seleccionado: {os.path.basename(file_path)}"
        )
        self._transcribe_btn.configure(state="normal")
        self._message_queue.put(Message("status", "Archivo cargado correctamente"))

    def _transcribe_file(self) -> None:
        if not self._selected_file:
            self._message_queue.put(
                Message("error", "Seleccione un archivo primero.")
            )
            return

        if self._identify_speakers and not self._use_whisper:
            self._message_queue.put(
                Message(
                    "error",
                    "La identificación de hablantes requiere el motor whisper.\n"
                    "Active 'Usar whisper' o desactive 'Identificar hablantes'.",
                )
            )
            return

        self._transcribe_btn.configure(state="disabled")
        self._import_btn.configure(state="disabled")
        self._progress.start()
        self._message_queue.put(Message("status", "Transcribiendo archivo..."))

        threading.Thread(target=self._run_transcription, daemon=True).start()

    def _run_transcription(self) -> None:
        try:
            file_path = Path(self._selected_file)

            if not file_path.exists():
                self._message_queue.put(Message("error", "El archivo ya no existe."))
                return

            if self._use_whisper:
                current_lang = whisper_lang(self._language)
                result = self._transcriber.transcribe_file_with_whisper(
                    str(file_path),
                    language=current_lang,
                    progress_callback=lambda p: self._message_queue.put(
                        Message("progress", p)
                    ),
                )
                self._message_queue.put(
                    Message("transcription_result", result)
                )
            else:
                result = self._transcriber.transcribe_file_with_google(
                    str(file_path),
                    language=self._language,
                    progress_callback=lambda p: self._message_queue.put(
                        Message("progress", p)
                    ),
                )
                self._message_queue.put(
                    Message("transcription_result", result)
                )

        except RuntimeError as exc:
            self._message_queue.put(Message("error", str(exc)))
        except Exception as exc:
            logger.exception("Error en transcripción de archivo: %s", exc)
            self._message_queue.put(
                Message("error", f"Error al transcribir: {exc}")
            )
        finally:
            self._message_queue.put(Message("progress_stop", None))
            self._message_queue.put(
                Message("transcribe_finished", None)
            )

    def set_language(self, google_code: str) -> None:
        self._language = google_code
