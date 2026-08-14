import { FileText, Captions, Braces, Copy } from "lucide-react";
import { Segment } from "../types";

interface Props {
  segments: Segment[] | null;
  fullText: string | null;
  filename: string;
}

export default function ExportPanel({ segments, fullText, filename }: Props) {
  const baseName = filename.replace(/\.[^.]+$/, "");

  const download = (content: string, ext: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}_transcripcion.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportTxt = () => {
    const text = segments
      ? segments
          .map((s) => {
            const spkr = s.speaker_id ? `[Hablante ${s.speaker_id}] ` : "";
            return `[${fmt(s.start)}-${fmt(s.end)}] ${spkr}${s.text}`;
          })
          .join("\n")
      : fullText || "";
    download(text, "txt", "text/plain");
  };

  const exportSrt = () => {
    if (!segments) return alert("Solo disponible con transcripción whisper.");
    let srt = "";
    segments.forEach((s, i) => {
      const spkr = s.speaker_id ? `[Hablante ${s.speaker_id}] ` : "";
      srt += `${i + 1}\n`;
      srt += `${srtTime(s.start)} --> ${srtTime(s.end)}\n`;
      srt += `${spkr}${s.text}\n\n`;
    });
    download(srt, "srt", "text/plain");
  };

  const exportJson = () => {
    if (!segments) return alert("Solo disponible con transcripción whisper.");
    download(
      JSON.stringify({ segments, fullText }, null, 2),
      "json",
      "application/json"
    );
  };

  const copy = () => {
    const text = segments
      ? segments.map((s) => s.text).join(" ")
      : fullText || "";
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="export-panel">
      <button onClick={exportTxt}><FileText size={16} /> TXT</button>
      <button onClick={exportSrt}><Captions size={16} /> SRT</button>
      <button onClick={exportJson}><Braces size={16} /> JSON</button>
      <button onClick={copy}><Copy size={16} /> Copiar</button>
    </div>
  );
}

function fmt(s: number) {
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1);
  return `${m}:${sec.padStart(4, "0")}`;
}

function srtTime(s: number) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  const ms = Math.floor((s % 1) * 1000);
  return `${pad(h)}:${pad(m)}:${pad(sec)},${pad3(ms)}`;
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}
function pad3(n: number) {
  return String(n).padStart(3, "0");
}
