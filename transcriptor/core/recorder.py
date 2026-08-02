"""Grabación de audio en vivo desde el micrófono."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, List, Optional

from ..config import (
    RECORDING_ENERGY_THRESHOLD,
    RECORDING_PAUSE_THRESHOLD,
    RECORDING_PHRASE_TIME_LIMIT,
    RECORDING_AMBIENT_ADJUST_DURATION,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AudioRecorder:
    """Grabadora de audio en vivo usando speech_recognition.

    Attributes:
        is_recording: Indica si la grabación está activa.
        is_paused: Indica si la grabación está en pausa.
        audio_frames: Lista de fragmentos de audio capturados.
        elapsed_seconds: Tiempo transcurrido desde el inicio.
    """

    def __init__(
        self,
        energy_threshold: int = RECORDING_ENERGY_THRESHOLD,
        pause_threshold: float = RECORDING_PAUSE_THRESHOLD,
        phrase_time_limit: int = RECORDING_PHRASE_TIME_LIMIT,
        ambient_duration: int = RECORDING_AMBIENT_ADJUST_DURATION,
    ) -> None:
        self._energy_threshold = energy_threshold
        self._pause_threshold = pause_threshold
        self._phrase_time_limit = phrase_time_limit
        self._ambient_duration = ambient_duration

        self.is_recording: bool = False
        self.is_paused: bool = False
        self.audio_frames: List[Any] = []
        self.elapsed_seconds: float = 0.0

        self._start_time: float = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_audio_callback: Optional[Callable[[Any], None]] = None

    def set_callback(self, callback: Callable[[Any], None]) -> None:
        """Establece un callback que recibe cada fragmento de audio capturado."""
        self._on_audio_callback = callback

    def check_microphone(self) -> bool:
        """Verifica si hay un micrófono disponible en el sistema."""
        try:
            import pyaudio

            p = pyaudio.PyAudio()
            try:
                p.get_default_input_device_info()
                return True
            finally:
                p.terminate()
        except Exception:
            logger.warning("No se detectó ningún micrófono en el sistema.")
            return False

    def start(self) -> None:
        """Inicia la grabación en un hilo separado."""
        if self.is_recording:
            logger.warning("La grabación ya está en curso.")
            return

        self.is_recording = True
        self.is_paused = False
        self.audio_frames.clear()
        self._start_time = time.time()
        self.elapsed_seconds = 0.0
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        logger.info("Grabación iniciada.")

    def pause(self) -> None:
        """Alterna entre pausar y reanudar la grabación."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            logger.info("Grabación pausada.")
        else:
            logger.info("Grabación reanudada.")

    def stop(self) -> None:
        """Detiene la grabación y espera a que el hilo termine."""
        self.is_recording = False
        self._stop_event.set()

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info(
            "Grabación finalizada. Fragmentos capturados: %d",
            len(self.audio_frames),
        )

    def _record_loop(self) -> None:
        """Bucle principal de grabación. Se ejecuta en un hilo separado."""
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self._energy_threshold
        recognizer.pause_threshold = self._pause_threshold

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self._ambient_duration,
                )

                while self.is_recording:
                    if self._stop_event.is_set():
                        break
                    if self.is_paused:
                        time.sleep(0.05)
                        continue

                    self._tick_timer()

                    try:
                        audio = recognizer.listen(
                            source,
                            timeout=1,
                            phrase_time_limit=self._phrase_time_limit,
                        )
                        self.audio_frames.append(audio)

                        if self._on_audio_callback is not None:
                            self._on_audio_callback(audio)

                    except sr.WaitTimeoutError:
                        self._tick_timer()
                        continue
        except OSError as exc:
            logger.error("Error de acceso al micrófono: %s", exc)
            self.is_recording = False
        except Exception as exc:
            logger.exception("Error inesperado en la grabación: %s", exc)
            self.is_recording = False

    def _tick_timer(self) -> None:
        """Actualiza el contador de tiempo transcurrido."""
        if not self.is_recording or self.is_paused:
            return
        self.elapsed_seconds = time.time() - self._start_time

    def export_to_wav(self, file_path: str) -> bool:
        """Exporta todos los frames de audio capturados a un archivo WAV.

        Args:
            file_path: Ruta de destino del archivo WAV.

        Returns:
            True si la exportación fue exitosa, False si no hay frames.
        """
        if not self.audio_frames:
            logger.warning("No hay audio para exportar.")
            return False

        try:
            combined = self._build_audio_segment()
            combined.export(file_path, format="wav")
            logger.info(
                "Grabación exportada a '%s' (%.1fs, %d frames).",
                file_path,
                combined.duration_seconds,
                len(self.audio_frames),
            )
            return True
        except Exception as exc:
            logger.error("Error al exportar grabación a WAV: %s", exc)
            return False

    def _build_audio_segment(self) -> "pydub.AudioSegment":
        """Construye un AudioSegment de pydub a partir de todos los frames."""
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for frame in self.audio_frames:
            raw = frame.get_raw_data()
            seg = AudioSegment(
                data=raw,
                sample_width=frame.sample_width,
                frame_rate=frame.sample_rate,
                channels=1,
            )
            combined += seg
        return combined
