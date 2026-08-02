import { useState } from "react";
import RecordingTab from "./components/RecordingTab";
import FileImportTab from "./components/FileImportTab";
import OcrTab from "./components/OcrTab";
import TranscriptionBox from "./components/TranscriptionBox";
import ExportPanel from "./components/ExportPanel";
import { Segment } from "./types";

type TabName = "recording" | "file" | "ocr";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabName>("recording");
  const [text, setText] = useState<string | null>(null);
  const [segments, setSegments] = useState<Segment[] | null>(null);
  const [speakers, setSpeakers] = useState(0);
  const [backend, setBackend] = useState("");
  const [filename, setFilename] = useState("transcripcion");

  const handleResult = (
    t: string | null,
    s: Segment[] | null,
    sp: number,
    bk: string
  ) => {
    setText(t);
    setSegments(s);
    setSpeakers(sp);
    setBackend(bk);
  };

  const handleOcr = (t: string) => {
    setText((prev) => (prev ? prev + "\n\n--- OCR ---\n" + t : "--- OCR ---\n" + t));
    setSegments(null);
    setSpeakers(0);
  };

  const tabs: { name: TabName; label: string }[] = [
    { name: "recording", label: "🎤 Grabación" },
    { name: "file", label: "📁 Archivo" },
    { name: "ocr", label: "🖼️ OCR" },
  ];

  return (
    <div className="app">
      <header>
        <h1>Transcriptor v2.1.0</h1>
        <span className="backend-badge">{backend}</span>
      </header>

      <nav className="tabs">
        {tabs.map((t) => (
          <button
            key={t.name}
            className={activeTab === t.name ? "tab active" : "tab"}
            onClick={() => setActiveTab(t.name)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {activeTab === "recording" && <RecordingTab onResult={handleResult} />}
        {activeTab === "file" && <FileImportTab onResult={handleResult} />}
        {activeTab === "ocr" && <OcrTab onResult={handleOcr} />}
      </main>

      <TranscriptionBox
        segments={segments}
        fullText={text}
        speakersDetected={speakers}
      />

      <ExportPanel segments={segments} fullText={text} filename={filename} />
    </div>
  );
}
