import { useState } from "react";
import { useAudioRecorder, extensionFromMimeType } from "../hooks/useAudioRecorder";
import { transcribeLive } from "../services/api";
import { Segment } from "../types";
import LanguageSelector from "./LanguageSelector";

interface Props {
  onResult: (
    text: string | null,
    segments: Segment[] | null,
    speakers: number,
    backend: string
  ) => void;
}

export default function RecordingTab({ onResult }: Props) {
  const { isRecording, isPaused, elapsed, error, start, pause, resume, stop } =
    useAudioRecorder();
  const [language, setLanguage] = useState("es");
  const [diarize, setDiarize] = useState(false);
  const [status, setStatus] = useState("");
  const [processing, setProcessing] = useState(false);

  const handleStart = () => {
    setStatus("Solicitando micrófono...");
    start();
  };

  const handleStop = async () => {
    setProcessing(true);
    setStatus("Procesando...");
    try {
      const blob = await stop();
      const ext = extensionFromMimeType(blob.type);
      const result = await transcribeLive(
        blob,
        `recording.${ext}`,
        language,
        diarize
      );
      onResult(
        result.fullText,
        result.segments,
        result.speakersDetected,
        result.backend
      );
      setStatus("Transcripción completada");
    } catch (e) {
      setStatus("Error: " + e);
    } finally {
      setProcessing(false);
    }
  };

  const togglePause = () => {
    if (isPaused) resume();
    else pause();
  };

  const display = `${String(Math.floor(elapsed / 60)).padStart(2, "0")}:${String(
    elapsed % 60
  ).padStart(2, "0")}`;

  return (
    <div className="tab-content">
      <div className="timer">{display}</div>
      <p className="status-text">
        {error ? error : status || "Listo para grabar"}
      </p>

      <div className="controls">
        <button
          className="btn-start"
          onClick={handleStart}
          disabled={isRecording || processing}
        >
          ▶ Iniciar Grabación
        </button>
        <button
          className="btn-stop"
          onClick={handleStop}
          disabled={!isRecording || processing}
        >
          ⏹ Finalizar
        </button>
        <button
          className="btn-pause"
          onClick={togglePause}
          disabled={!isRecording || processing}
        >
          {isPaused ? "▶ Reanudar" : "⏸ Pausar"}
        </button>
      </div>

      <div className="options">
        <LanguageSelector language={language} onChange={setLanguage} />
        <label>
          <input
            type="checkbox"
            checked={diarize}
            onChange={(e) => setDiarize(e.target.checked)}
          />
          🔊 Identificar hablantes
        </label>
      </div>
    </div>
  );
}
