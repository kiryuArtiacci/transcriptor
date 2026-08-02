"""Pestaña de grabación de audio en vivo."""

from __future__ import annotations

import os
import queue
import tempfile
import threading
from pathlib import Path
from typing import Any

import customtkinter as ctk

from ..config import (
    DEFAULT_LANGUAGE,
    RECORDING_ENERGY_THRESHOLD,
    RECORDING_PAUSE_THRESHOLD,
    RECORDING_PHRASE_TIME_LIMIT,
    RECORDING_AMBIENT_ADJUST_DURATION,
    whisper_lang,
)
from ..core.recorder import AudioRecorder
from ..core.transcriber import Transcriber
from ..utils.logger import get_logger
from .widgets import Message, TimerLabel

logger = get_logger(__name__)


class RecordingTab(ctk.CTkFrame):
    """Pestaña para grabación de audio en vivo con transcripción simultánea."""

    def __init__(
        self,
        master: Any,
        message_queue: queue.Queue,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._message_queue = message_queue
        self._language = "es-ES"
        self._identify_speakers = False

        self._recorder = AudioRecorder(
            energy_threshold=RECORDING_ENERGY_THRESHOLD,
            pause_threshold=RECORDING_PAUSE_THRESHOLD,
            phrase_time_limit=RECORDING_PHRASE_TIME_LIMIT,
            ambient_duration=RECORDING_AMBIENT_ADJUST_DURATION,
        )
        self._recorder.set_callback(self._on_audio_captured)

        self._transcriber = Transcriber()
        self._has_microphone = self._recorder.check_microphone()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        mic_status = (
            "Micrófono detectado"
            if self._has_microphone
            else "Micrófono no detectado"
        )
        mic_color = "green" if self._has_microphone else "red"

        self._mic_label = ctk.CTkLabel(
            controls_frame,
            text=mic_status,
            font=ctk.CTkFont(size=14),
            text_color=mic_color,
        )
        self._mic_label.pack(pady=10)

        btn_frame = ctk.CTkFrame(controls_frame)
        btn_frame.pack(pady=20)

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Iniciar Grabación",
            command=self._start_recording,
            fg_color="green",
            width=200,
            height=40,
        )
        self._start_btn.pack(side="left", padx=10)

        if not self._has_microphone:
            self._start_btn.configure(
                state="disabled",
                text="Micrófono no disponible",
            )

        self._pause_btn = ctk.CTkButton(
            btn_frame,
            text="⏸ Pausar",
            command=self._toggle_pause,
            fg_color="orange",
            state="disabled",
            width=150,
            height=40,
        )
        self._pause_btn.pack(side="left", padx=10)

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Finalizar",
            command=self._stop_recording,
            fg_color="red",
            state="disabled",
            width=150,
            height=40,
        )
        self._stop_btn.pack(side="left", padx=10)

        self._timer_display = ctk.CTkLabel(
            controls_frame,
            text="00:00",
            font=ctk.CTkFont(size=48, weight="bold"),
        )
        self._timer_display.pack(pady=20)
        self._timer = TimerLabel(self._timer_display)

        self._status_label = ctk.CTkLabel(
            controls_frame,
            text="Presione 'Iniciar Grabación' para comenzar",
            font=ctk.CTkFont(size=14),
        )
        self._status_label.pack(pady=10)

        self._speaker_switch = ctk.CTkSwitch(
            controls_frame,
            text="🔊 Identificar hablantes al finalizar",
            command=lambda: setattr(self, '_identify_speakers', self._speaker_switch.get() == 1),
        )
        self._speaker_switch.pack(pady=5)

    def _start_recording(self) -> None:
        if not self._has_microphone:
            self._message_queue.put(Message("error", "No se detectó ningún micrófono."))
            return

        self._recorder.start()
        self._timer.start(self)

        self._start_btn.configure(state="disabled")
        self._pause_btn.configure(state="normal")
        self._stop_btn.configure(state="normal")
        self._pause_btn.configure(text="⏸ Pausar")

        self._message_queue.put(Message("status", "Grabando..."))

    def _toggle_pause(self) -> None:
        self._recorder.pause()
        if self._recorder.is_paused:
            self._pause_btn.configure(text="▶ Reanudar")
            self._timer.pause()
            self._message_queue.put(Message("status", "Grabación pausada"))
        else:
            self._pause_btn.configure(text="⏸ Pausar")
            self._timer.resume()
            self._message_queue.put(Message("status", "Grabando..."))

    def _stop_recording(self) -> None:
        self._recorder.stop()
        self._timer.stop()

        self._start_btn.configure(
            state="normal" if self._has_microphone else "disabled"
        )
        self._pause_btn.configure(state="disabled")
        self._stop_btn.configure(state="disabled")
        self._pause_btn.configure(text="⏸ Pausar")

        if not self._recorder.audio_frames:
            self._message_queue.put(
                Message("status", "No se capturó audio.")
            )
            return

        self._message_queue.put(
            Message("status", "Grabación finalizada. Procesando...")
        )
        self._message_queue.put(Message("progress_start", None))

        if self._identify_speakers:
            threading.Thread(
                target=self._process_with_diarization,
                daemon=True,
            ).start()
        else:
            threading.Thread(
                target=self._process_recorded_audio,
                daemon=True,
            ).start()

    def _on_audio_captured(self, audio_data: Any) -> None:
        text = self._transcriber.transcribe_google(audio_data, language=self._language)
        if text:
            self._message_queue.put(Message("transcription", text))

    def _process_recorded_audio(self) -> None:
        full_parts = []
        frames = self._recorder.audio_frames
        total = len(frames)

        import speech_recognition as sr

        recognizer = sr.Recognizer()

        for i, audio in enumerate(frames):
            try:
                text = recognizer.recognize_google(audio, language=self._language)
                full_parts.append(text)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                logger.error("Error en reprocesamiento: %s", exc)
                continue

            self._message_queue.put(Message("progress", (i + 1) / total))

        final_text = " ".join(full_parts).strip()
        if final_text:
            self._message_queue.put(Message("final_transcription", final_text))
        else:
            self._message_queue.put(Message("status", "No se pudo transcribir el audio"))

        self._message_queue.put(Message("progress_stop", None))

    def _process_with_diarization(self) -> None:
        """Post-procesa la grabación con whisper + diarización de hablantes."""
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=".wav", prefix="transcriptor_rec_"
            )
            os.close(fd)

            ok = self._recorder.export_to_wav(temp_path)
            if not ok:
                self._message_queue.put(
                    Message("error", "No se pudo exportar el audio grabado.")
                )
                return

            wl = whisper_lang(self._language)
            self._message_queue.put(
                Message("status", "Transcribiendo con whisper + diarización...")
            )

            result = self._transcriber.transcribe_file_with_whisper(
                temp_path,
                language=wl,
                progress_callback=lambda p: self._message_queue.put(
                    Message("progress", p)
                ),
            )
            self._message_queue.put(Message("transcription_result", result))

        except Exception as exc:
            logger.exception("Error en diarización de grabación: %s", exc)
            self._message_queue.put(
                Message("error", f"Error en diarización: {exc}")
            )
        finally:
            if temp_path is not None and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            self._message_queue.put(Message("progress_stop", None))

    def update_status(self, text: str) -> None:
        self._status_label.configure(text=text)

    def set_language(self, google_code: str) -> None:
        self._language = google_code
