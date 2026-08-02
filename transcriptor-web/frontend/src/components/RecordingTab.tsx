import { useState } from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
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
  const { isRecording, isPaused, elapsed, start, pause, resume, stop } =
    useAudioRecorder();
  const [language, setLanguage] = useState("es");
  const [diarize, setDiarize] = useState(false);
  const [status, setStatus] = useState("");
  const [preview, setPreview] = useState("");

  const toggleRecording = async () => {
    if (isRecording) {
      setStatus("Procesando...");
      const blob = await stop();
      try {
        const result = await transcribeLive(blob, "recording.wav", language, diarize);
        onResult(
          result.fullText,
          result.segments,
          result.speakersDetected,
          result.backend
        );
        setStatus("Transcripción completada");
      } catch (e) {
        setStatus("Error: " + e);
      }
    } else {
      setPreview("");
      setStatus("Grabando...");
      start((text) => setPreview((p) => p + " " + text));
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
      <p className="status-text">{status || "Listo para grabar"}</p>

      <div className="controls">
        <button
          className={isRecording ? "btn-stop" : "btn-start"}
          onClick={toggleRecording}
        >
          {isRecording ? "⏹ Finalizar" : "▶ Iniciar Grabación"}
        </button>
        {isRecording && (
          <button className="btn-pause" onClick={togglePause}>
            {isPaused ? "▶ Reanudar" : "⏸ Pausar"}
          </button>
        )}
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

      {preview && (
        <div className="preview">
          <strong>Preview:</strong> {preview}
        </div>
      )}
    </div>
  );
}
