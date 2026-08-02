import { useState, useRef } from "react";
import { transcribeFile } from "../services/api";
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

export default function FileImportTab({ onResult }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("es");
  const [diarize, setDiarize] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setStatus(`Archivo: ${f.name} (${(f.size / 1024 / 1024).toFixed(1)} MB)`);
    }
  };

  const transcribe = async () => {
    if (!file) return;
    setLoading(true);
    setStatus("Transcribiendo...");
    try {
      const result = await transcribeFile(file, language, diarize);
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
      setLoading(false);
    }
  };

  return (
    <div className="tab-content">
      <div className="file-upload">
        <input
          type="file"
          accept="audio/*"
          onChange={handleFile}
          ref={fileRef}
          style={{ display: "none" }}
        />
        <button onClick={() => fileRef.current?.click()} className="btn-upload">
          📁 Importar archivo de audio
        </button>
      </div>

      {file && <p className="status-text">{status}</p>}

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

      <button
        onClick={transcribe}
        disabled={!file || loading}
        className="btn-start"
      >
        {loading ? "⏳ Transcribiendo..." : "🎙️ Transcribir"}
      </button>
    </div>
  );
}
