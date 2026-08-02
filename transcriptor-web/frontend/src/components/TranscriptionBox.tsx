import React from "react";
import { Segment } from "../types";

interface Props {
  segments: Segment[] | null;
  fullText: string | null;
  speakersDetected: number;
}

export default function TranscriptionBox({
  segments,
  fullText,
  speakersDetected,
}: Props) {
  const speakerColors = ["#4fc3f7", "#ff8a65", "#81c784", "#ba68c8"];

  const getText = () => {
    if (segments && segments.length > 0) {
      return segments
        .map((s) => {
          const spkr = s.speaker_id ? `[Hablante ${s.speaker_id}] ` : "";
          return `[${fmt(s.start)}-${fmt(s.end)}] ${spkr}${s.text}`;
        })
        .join("\n");
    }
    return fullText || "";
  };

  const getHtml = () => {
    if (!segments || segments.length === 0) return fullText || "";
    return segments
      .map((s) => {
        const color = s.speaker_id
          ? speakerColors[(s.speaker_id - 1) % speakerColors.length]
          : "#ccc";
        const spkr = s.speaker_id
          ? `<span style="color:${color};font-weight:bold">[Hablante ${s.speaker_id}]</span> `
          : "";
        return (
          `<span style="color:#888">[${fmt(s.start)}-${fmt(s.end)}]</span> ` +
          `${spkr}${esc(s.text)}`
        );
      })
      .join("<br/>");
  };

  return (
    <div className="transcription-box">
      <div className="transcription-header">
        <strong>Transcripción</strong>
        {speakersDetected > 1 && (
          <span className="speaker-badge">
            {speakersDetected} hablante(s) detectado(s)
          </span>
        )}
      </div>
      <div
        className="transcription-text"
        dangerouslySetInnerHTML={{ __html: getHtml() }}
      />
      <textarea
        readOnly
        value={getText()}
        style={{ display: "none" }}
        id="transcription-raw"
      />
    </div>
  );
}

function fmt(s: number) {
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1);
  return `${m}:${sec.padStart(4, "0")}`;
}

function esc(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
