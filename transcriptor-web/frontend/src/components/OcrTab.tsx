import { useState, useRef } from "react";
import { Image as ImageIcon, LoaderCircle, ScanText } from "lucide-react";
import { extractOcr } from "../services/api";

interface Props {
  onResult: (text: string) => void;
}

const OCR_LANGUAGES: Record<string, string> = {
  "Español (spa)": "spa",
  "English (eng)": "eng",
  "Français (fra)": "fra",
  "Deutsch (deu)": "deu",
};

export default function OcrTab({ onResult }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [language, setLanguage] = useState("spa");
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const runOcr = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const result = await extractOcr(file, language);
      onResult(result.text);
    } catch (e) {
      onResult("Error: " + e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-content">
      <div className="file-upload">
        <input
          type="file"
          accept="image/*,.pdf"
          onChange={handleFile}
          ref={fileRef}
          style={{ display: "none" }}
        />
        <button onClick={() => fileRef.current?.click()} className="btn-upload">
          <ImageIcon size={16} /> Cargar imagen
        </button>
      </div>

      {preview && (
        <img src={preview} alt="preview" className="preview-img" />
      )}

      <div className="options">
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="lang-select"
        >
          {Object.entries(OCR_LANGUAGES).map(([name, code]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={runOcr}
        disabled={!file || loading}
        className="btn-start"
      >
        {loading ? (
          <LoaderCircle size={16} className="spin" />
        ) : (
          <ScanText size={16} />
        )}
        {loading ? "Extrayendo..." : "Extraer texto"}
      </button>
    </div>
  );
}
