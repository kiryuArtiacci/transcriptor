"""Whisper Microservice — Transcripción y diarización vía REST."""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transcriptor.config import whisper_lang
from transcriptor.core.transcriber import Transcriber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper-service")

app = Flask(__name__)
_transcriber: Transcriber | None = None


def _get_transcriber() -> Transcriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber()
    return _transcriber


def _segments_to_dict(segments: list) -> list:
    return [
        {
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text,
            "speaker_id": s.speaker_id,
        }
        for s in segments
    ]


def _save_upload(file) -> str:
    """Guarda el archivo subido preservando su extensión original."""
    original_name = file.filename or "audio.wav"
    ext = os.path.splitext(original_name)[1] or ".wav"
    fd, temp_path = tempfile.mkstemp(suffix=ext, prefix="whisper_svc_")
    os.close(fd)
    file.save(temp_path)
    return temp_path


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "whisper-transcriber"})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Transcribe un archivo de audio con whisper.

    Espera multipart: file (obligatorio), language (opcional, default 'es'),
    diarize (opcional, default 'false').
    """
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]
    language = request.form.get("language", "es")
    diarize = request.form.get("diarize", "false").lower() == "true"
    lang_code = whisper_lang(language)

    temp_path = _save_upload(file)

    try:
        tc = _get_transcriber()
        result = tc.transcribe_file_with_whisper(
            temp_path,
            language=lang_code,
            progress_callback=None,
        )

        return jsonify({
            "full_text": result.full_text,
            "segments": _segments_to_dict(result.segments),
            "language": result.language,
            "duration": round(result.duration, 2),
            "backend": result.backend,
            "speakers_detected": len(
                {s.speaker_id for s in result.segments if s.speaker_id}
            ),
        })
    except Exception as exc:
        logger.exception("Error en /transcribe: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.route("/transcribe-google", methods=["POST"])
def transcribe_google():
    """Transcribe con Google STT (rápido, sin diarización)."""
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]
    language = request.form.get("language", "es-ES")

    temp_path = _save_upload(file)

    try:
        tc = _get_transcriber()
        result = tc.transcribe_file_with_google(
            temp_path,
            language=language,
            progress_callback=None,
        )

        return jsonify({
            "full_text": result.full_text,
            "segments": _segments_to_dict(result.segments),
            "language": result.language,
            "duration": round(result.duration, 2),
            "backend": result.backend,
        })
    except Exception as exc:
        logger.exception("Error en /transcribe-google: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
