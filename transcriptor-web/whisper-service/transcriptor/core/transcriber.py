"""Motor de transcripción de voz a texto.

Soporta dos backends:
  - Google Speech Recognition (rápido, requiere internet, gratuito).
  - faster-whisper (offline, local, más preciso, genera timestamps).

Incluye diarización de hablantes con resemblyzer (opcional).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from ..config import (
    DIAR_MIN_SEGMENT_MS,
    DIAR_MIN_SAMPLES,
    DIAR_RMS_THRESHOLD,
    DIAR_TIME_GAP_S,
    DIAR_GAP_PENALTY_MAX,
    DIAR_GAP_PENALTY_RATE,
    DIAR_THRESHOLD_FLOOR,
    DIAR_THRESHOLD_CAP,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TranscriptionSegment:
    """Segmento de transcripción con información de tiempo y hablante."""

    text: str
    start: float
    end: float
    speaker_id: int = 0


@dataclass
class TranscriptionResult:
    """Resultado completo de una transcripción."""

    full_text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float = 0.0
    backend: str = ""


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class Transcriber:
    """Motor de transcripción multibackend."""

    def __init__(self) -> None:
        self._whisper_model = None
        self._whisper_model_size: Optional[str] = None
        self._voice_encoder = None
        self._diarization_available = False
        self._using_resemblyzer = False

    def transcribe_google(
        self,
        audio_data: Any,
        language: str = "es-ES",
    ) -> Optional[str]:
        """Transcribe un fragmento de audio usando Google Speech Recognition.

        Args:
            audio_data: Datos de audio capturados por speech_recognition.
            language: Código de idioma (ej. 'es-ES').

        Returns:
            Texto transcrito, o None si no se pudo reconocer.
        """
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        try:
            text = recognizer.recognize_google(audio_data, language=language)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            logger.error("Error en Google STT: %s", exc)
            return None

    def transcribe_file_with_google(
        self,
        wav_path: str | Path,
        language: str = "es-ES",
        chunk_duration: int | None = None,
        progress_callback: Any = None,
    ) -> TranscriptionResult:
        """Transcribe un archivo WAV completo usando Google STT.

        Args:
            wav_path: Ruta al archivo WAV.
            language: Código de idioma.
            chunk_duration: Duración de cada fragmento en segundos.
            progress_callback: Callable(progress: float) para reportar avance.

        Returns:
            TranscriptionResult con el texto completo y segmentos.
        """
        import speech_recognition as sr

        from ..config import FILE_CHUNK_DURATION
        from .audio_processor import get_audio_duration, get_chunk_count, cleanup_temp_wav

        if chunk_duration is None:
            chunk_duration = FILE_CHUNK_DURATION

        recognizer = sr.Recognizer()
        wav_path = str(wav_path)
        segments: List[TranscriptionSegment] = []
        is_temp = False

        try:
            source = sr.AudioFile(wav_path)
        except Exception:
            from .audio_processor import convert_to_wav

            logger.info("Convirtiendo archivo a WAV para transcripción...")
            wav_path = convert_to_wav(wav_path)
            is_temp = True
            source = sr.AudioFile(wav_path)

        duration = get_audio_duration(wav_path)
        total_chunks = get_chunk_count(wav_path, chunk_duration)

        logger.info(
            "Transcribiendo archivo con Google STT (%d fragmentos, %.1fs)...",
            total_chunks,
            duration,
        )

        with source as src:
            for i in range(total_chunks):
                remaining = duration - i * chunk_duration
                if remaining <= 0:
                    break

                chunk_size = min(chunk_duration, remaining)
                offset = i * chunk_duration

                try:
                    audio = recognizer.record(src, duration=chunk_size)
                    text = recognizer.recognize_google(audio, language=language)
                    if text.strip():
                        segments.append(
                            TranscriptionSegment(
                                text=text,
                                start=offset,
                                end=offset + chunk_size,
                            )
                        )
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as exc:
                    logger.error("Google STT error en fragmento %d: %s", i, exc)
                    continue
                except Exception as exc:
                    logger.warning("Error en fragmento %d: %s", i, exc)
                    continue

                if progress_callback is not None:
                    progress_callback((i + 1) / total_chunks)

        if is_temp:
            cleanup_temp_wav(wav_path)

        full_text = " ".join(seg.text for seg in segments)
        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=language,
            duration=duration,
            backend="google",
        )

    def transcribe_file_with_whisper(
        self,
        file_path: str | Path,
        language: str = "es",
        model_size: str | None = None,
        progress_callback: Any = None,
    ) -> TranscriptionResult:
        """Transcribe un archivo de audio usando faster-whisper (offline).

        Args:
            file_path: Ruta al archivo de audio (cualquier formato soportado por whisper).
            language: Código de idioma para whisper (ej. 'es', 'en').
            model_size: Tamaño del modelo ('tiny', 'base', 'small', 'medium', 'large').
            progress_callback: Callable(progress: float) para reportar avance.

        Returns:
            TranscriptionResult con texto completo y segmentos con timestamps.

        Raises:
            RuntimeError: Si faster-whisper no está instalado.
        """
        from ..config import WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE

        if model_size is None:
            model_size = WHISPER_MODEL_SIZE

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper no está instalado. "
                "Ejecute: pip install faster-whisper"
            ) from exc

        if self._whisper_model is None or self._whisper_model_size != model_size:
            logger.info("Cargando modelo whisper '%s'...", model_size)
            self._whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type=WHISPER_COMPUTE_TYPE,
            )
            self._whisper_model_size = model_size

        file_path = str(file_path)
        is_temp_wav = False

        if not file_path.lower().endswith(".wav"):
            from .audio_processor import convert_to_wav

            logger.info("Convirtiendo a WAV para diarización...")
            file_path = convert_to_wav(file_path)
            is_temp_wav = True

        logger.info("Transcribiendo '%s' con whisper (%s)...", file_path, model_size)

        segments_out, info = self._whisper_model.transcribe(
            file_path,
            language=language,
            beam_size=5,
            vad_filter=False,
        )

        segments: List[TranscriptionSegment] = []
        full_parts: List[str] = []

        segment_list = list(segments_out)
        total_segments = max(len(segment_list), 1)

        for idx, seg in enumerate(segment_list):
            text = seg.text.strip()
            if text:
                segments.append(
                    TranscriptionSegment(
                        text=text,
                        start=seg.start,
                        end=seg.end,
                    )
                )
                full_parts.append(text)

            if progress_callback is not None:
                progress_callback((idx + 1) / total_segments)

        full_text = " ".join(full_parts)

        if len(segments) >= 2:
            logger.info(
                "Iniciando diarización con %d segmentos de texto.", len(segments)
            )
            segments = self._diarize_segments(file_path, segments)
        else:
            logger.info(
                "Solo %d segmento(s) de whisper — diarización omitida.", len(segments)
            )

        if is_temp_wav:
            from .audio_processor import cleanup_temp_wav

            cleanup_temp_wav(file_path)

        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=language,
            duration=info.duration,
            backend=f"whisper-{model_size}",
        )

    def _ensure_voice_encoder(self) -> bool:
        """Inicializa el codificador de voz. Prioriza resemblyzer; fallback a FFT.

        Returns:
            True si algún método de diarización está disponible.
        """
        if self._diarization_available:
            return True

        try:
            from resemblyzer import VoiceEncoder

            self._voice_encoder = VoiceEncoder()
            self._diarization_available = True
            self._using_resemblyzer = True
            logger.info("Diarización de hablantes habilitada (resemblyzer).")
            return True
        except (ImportError, ModuleNotFoundError):
            logger.info("resemblyzer no disponible. Usando diarización por espectro (numpy).")
            self._diarization_available = True
            self._using_resemblyzer = False
            return True

    def _diarize_segments(
        self,
        audio_path: str,
        segments: List[TranscriptionSegment],
    ) -> List[TranscriptionSegment]:
        """Asigna etiquetas de hablante a cada segmento usando embeddings de voz.

        Args:
            audio_path: Ruta al archivo de audio original.
            segments: Lista de segmentos transcritos con timestamps.

        Returns:
            La misma lista de segmentos con speaker_id actualizado.
        """
        if not self._ensure_voice_encoder():
            return segments

        import numpy as np
        from pydub import AudioSegment

        try:
            audio = (
                AudioSegment.from_file(audio_path)
                .set_channels(1)
                .set_frame_rate(16000)
            )
        except Exception as exc:
            logger.warning("No se pudo cargar el audio para diarización: %s", exc)
            return segments

        all_samples = np.array(
            audio.get_array_of_samples(), dtype=np.float32
        ) / float(2 ** (8 * audio.sample_width - 1))
        global_rms = float(np.sqrt(np.mean(all_samples ** 2)))
        rms_threshold = max(global_rms * 0.25, DIAR_RMS_THRESHOLD)
        logger.info(
            "RMS global: %.5f — umbral: %.5f — %d segmentos a procesar",
            global_rms,
            rms_threshold,
            len(segments),
        )

        embeddings: List[np.ndarray] = []
        valid_indices: List[int] = []

        for i, seg in enumerate(segments):
            start_ms = max(0, int(seg.start * 1000))
            end_ms = min(len(audio), int(seg.end * 1000))
            duration_ms = end_ms - start_ms

            if duration_ms < DIAR_MIN_SEGMENT_MS:
                continue

            chunk = audio[start_ms:end_ms]
            max_val = float(2 ** (8 * chunk.sample_width - 1))
            samples = np.array(
                chunk.get_array_of_samples(), dtype=np.float32
            ) / max_val

            if len(samples) < DIAR_MIN_SAMPLES:
                continue

            rms = np.sqrt(np.mean(samples ** 2))
            if rms < rms_threshold:
                continue

            try:
                if self._using_resemblyzer:
                    embed = self._voice_encoder.embed_utterance(samples)
                else:
                    embed = self._extract_voice_features(samples, 16000)
                embeddings.append(embed)
                valid_indices.append(i)
            except Exception as exc:
                logger.debug("Embedding fallido en segmento %d: %s", i, exc)
                continue

        if len(embeddings) < 2:
            logger.info(
                "Solo %d/%d segmentos válidos para diarización — omitida.",
                len(embeddings),
                len(segments),
            )
            return segments

        threshold = self._compute_adaptive_threshold(embeddings)
        time_gaps = [
            segments[idx].start
            for idx in valid_indices
        ]
        labels = self._cluster_by_similarity(
            embeddings, threshold=threshold, time_starts=time_gaps
        )

        for idx, label in zip(valid_indices, labels):
            segments[idx].speaker_id = label + 1

        unique_speakers = len(set(labels))
        logger.info(
            "Diarización completada: %d hablante(s) detectado(s) en %d segmentos.",
            unique_speakers,
            len(valid_indices),
        )
        return segments

    @staticmethod
    def _extract_voice_features(
        samples: "np.ndarray",
        sample_rate: int,
        n_mfcc: int = 7,
        n_mels: int = 26,
    ) -> "np.ndarray":
        """Extrae features robustas para diarización: MFCC low-order + prosódicas.

        Pipeline: pre-énfasis → framing 25ms/10ms → Hamming → FFT → mel filterbank
        → log → DCT (solo primeros 7 MFCC, envolvente espectral)
        → + ZCR (zero-crossing rate, sobrevive compresión narrowband)
        → + RMS energy (intensidad, clave en llamadas telefónicas)
        → + Spectral Centroid (brillo del timbre)
        → + Spectral Flatness (tonalidad vs ruido)

        Args:
            samples: Array numpy 1D con audio mono normalizado (float32).
            sample_rate: Frecuencia de muestreo en Hz.
            n_mfcc: Coeficientes cepstrales (7, solo envolvente).
            n_mels: Filtros mel.

        Returns:
            Vector normalizado de (n_mfcc * 3 + 4) dimensiones.
            Ceros si el audio es demasiado corto.
        """
        import numpy as np

        pre_emphasis = 0.97
        emphasized = samples.copy()
        emphasized[1:] -= pre_emphasis * samples[:-1]

        frame_len = int(0.025 * sample_rate)
        frame_step = int(0.010 * sample_rate)
        n_frames = max(1, (len(emphasized) - frame_len) // frame_step + 1)

        if n_frames < 3 or frame_len < 16:
            return np.zeros(n_mfcc * 3 + 4, dtype=np.float32)

        window = 0.54 - 0.46 * np.cos(
            2.0 * np.pi * np.arange(frame_len) / (frame_len - 1)
        )

        frames = np.zeros((n_frames, frame_len), dtype=np.float32)
        for i in range(n_frames):
            start = i * frame_step
            frames[i] = emphasized[start : start + frame_len] * window

        n_fft = 512
        mag_spec = np.abs(np.fft.rfft(frames, n=n_fft))
        power_spec = mag_spec ** 2
        n_freq = n_fft // 2 + 1

        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)

        zcr_frames = np.zeros(n_frames, dtype=np.float32)
        rms_frames = np.zeros(n_frames, dtype=np.float32)
        centroid_frames = np.zeros(n_frames, dtype=np.float32)
        flatness_frames = np.zeros(n_frames, dtype=np.float32)

        for i in range(n_frames):
            frame_data = frames[i]
            zcr_frames[i] = np.sum(
                np.abs(np.diff(np.sign(frame_data)))
            ) / (2.0 * frame_len)

            rms_frames[i] = np.sqrt(np.mean(frame_data ** 2))

            total_power = np.sum(power_spec[i])
            if total_power > 1e-12:
                centroid_frames[i] = np.sum(freqs * power_spec[i]) / total_power
                geo_mean = np.exp(np.mean(np.log(power_spec[i] + 1e-12)))
                arith_mean = total_power / n_freq
                flatness_frames[i] = (
                    geo_mean / (arith_mean + 1e-12) if arith_mean > 1e-12 else 0.0
                )
            else:
                centroid_frames[i] = 0.0
                flatness_frames[i] = 1.0

        low_mel = 2595.0 * np.log10(1.0 + 100.0 / 700.0)
        high_mel = 2595.0 * np.log10(1.0 + (sample_rate / 2.0) / 700.0)
        mel_pts = np.linspace(low_mel, high_mel, n_mels + 2)
        hz_pts = 700.0 * (10.0 ** (mel_pts / 2595.0) - 1.0)
        bins = np.floor((n_freq - 1) * hz_pts / (sample_rate / 2.0)).astype(int)
        bins = np.clip(bins, 0, n_freq - 1)

        fbank = np.zeros((n_mels, n_freq), dtype=np.float32)
        for m in range(1, n_mels + 1):
            for k in range(bins[m - 1], bins[m]):
                denom = max(bins[m] - bins[m - 1], 1)
                fbank[m - 1, k] = (k - bins[m - 1]) / denom
            for k in range(bins[m], bins[m + 1] + 1):
                denom = max(bins[m + 1] - bins[m], 1)
                fbank[m - 1, k] = (bins[m + 1] - k) / denom

        mel_energy = np.dot(mag_spec, fbank.T)
        mel_energy = np.log(mel_energy + 1e-10)

        mfcc = np.zeros((n_frames, n_mfcc), dtype=np.float32)
        col_indices = np.arange(n_mels, dtype=np.float32)
        for k in range(n_mfcc):
            mfcc[:, k] = np.sum(
                mel_energy * np.cos(np.pi * k * (col_indices + 0.5) / n_mels),
                axis=1,
            )

        mfcc_mean = np.mean(mfcc, axis=0)
        mfcc_std = np.std(mfcc, axis=0)

        half = max(n_frames // 2, 1)
        delta = np.mean(mfcc[half:], axis=0) - np.mean(mfcc[:half], axis=0)

        zcr_mean = np.mean(zcr_frames)
        rms_mean = np.mean(rms_frames)
        centroid_mean = np.mean(centroid_frames) / (sample_rate / 2.0)
        flatness_mean = np.mean(flatness_frames)

        prosodic = np.array(
            [zcr_mean, rms_mean * 10.0, centroid_mean, flatness_mean],
            dtype=np.float32,
        )

        features = np.concatenate(
            [mfcc_mean, mfcc_std, delta, prosodic]
        ).astype(np.float32)

        norm = np.linalg.norm(features)
        if norm > 0:
            features /= norm

        return features

    @staticmethod
    def _compute_adaptive_threshold(embeddings: list) -> float:
        """Umbral de similitud basado en percentil 75.

        Estrategia: en una conversación con N hablantes, los pares
        misma-persona tienen similitud alta (~percentil superior),
        mientras que los pares distinta-persona caen en el cuartil
        inferior. El P75 separa naturalmente ambos grupos.

        Args:
            embeddings: Lista de vectores normalizados.

        Returns:
            Umbral entre 0.45 y 0.88 (P75 cap).
        """
        import numpy as np

        emb = np.array(embeddings, dtype=np.float32)
        sims = emb @ emb.T

        n = len(embeddings)
        off_diag = []
        for i in range(n):
            for j in range(i + 1, n):
                off_diag.append(sims[i, j])

        if not off_diag:
            return 0.60

        p75 = float(np.percentile(off_diag, 75))
        threshold = max(DIAR_THRESHOLD_FLOOR, min(DIAR_THRESHOLD_CAP, p75))
        logger.debug(
            "Umbral P75: %.3f (valores: %.3f..%.3f)",
            threshold,
            min(off_diag),
            max(off_diag),
        )
        return threshold

    @staticmethod
    def _cluster_by_similarity(
        embeddings: list,
        threshold: float = 0.75,
        time_starts: list | None = None,
    ) -> list:
        """Agrupa embeddings de voz por similitud de coseno usando union-find.

        Aplica penalización temporal: segmentos con >5s de separación
        reducen su similitud un 20% (misma persona no suele tener
        pausas largas entre intervenciones en una conversación).

        Args:
            embeddings: Lista de vectores NumPy normalizados.
            threshold: Umbral de similitud (0.0-1.0).
            time_starts: Tiempos de inicio de cada segmento en segundos.

        Returns:
            Lista de etiquetas de clúster (enteros consecutivos desde 0).
        """
        import numpy as np

        n = len(embeddings)
        emb = np.array(embeddings, dtype=np.float32)

        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb /= norms

        sim = emb @ emb.T

        if time_starts is not None and len(time_starts) == n:
            for i in range(n):
                for j in range(i + 1, n):
                    gap = abs(time_starts[j] - time_starts[i])
                    if gap > DIAR_TIME_GAP_S:
                        penalty = 1.0 - min(DIAR_GAP_PENALTY_MAX, (gap - DIAR_TIME_GAP_S) * DIAR_GAP_PENALTY_RATE)
                        sim[i, j] *= penalty
                        sim[j, i] *= penalty

        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for i in range(n):
            for j in range(i + 1, n):
                if sim[i, j] > threshold:
                    union(i, j)

        label_map: dict[int, int] = {}
        labels: list[int] = []
        for i in range(n):
            root = find(i)
            if root not in label_map:
                label_map[root] = len(label_map)
            labels.append(label_map[root])

        return labels

    @staticmethod
    def segments_to_srt(segments: List[TranscriptionSegment]) -> str:
        """Convierte una lista de segmentos a formato SRT (subtítulos).

        Args:
            segments: Lista de segmentos de transcripción.

        Returns:
            Contenido en formato SRT.
        """

        lines: List[str] = []
        for i, seg in enumerate(segments, start=1):
            lines.append(str(i))
            lines.append(
                f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}"
            )
            speaker_prefix = f"[Hablante {seg.speaker_id}] " if seg.speaker_id else ""
            lines.append(f"{speaker_prefix}{seg.text}")
            lines.append("")

        return "\n".join(lines)
