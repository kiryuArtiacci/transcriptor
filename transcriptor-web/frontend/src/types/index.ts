export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker_id: number;
}

export interface TranscriptionResult {
  fullText: string;
  segments: Segment[];
  language: string;
  duration: number;
  backend: string;
  speakersDetected: number;
}

export interface OcrResult {
  text: string;
}

export interface WsMessage {
  type: string;
  text?: string;
  fullText?: string;
  segments?: Segment[];
  speakersDetected?: number;
  backend?: string;
  duration?: number;
}

export const LANGUAGES: Record<string, string> = {
  Español: "es-ES",
  English: "en-US",
  Français: "fr-FR",
  Deutsch: "de-DE",
  Português: "pt-BR",
  Italiano: "it-IT",
};

export const OCR_LANGUAGES: Record<string, string> = {
  "Español": "spa",
  "English": "eng",
  "Français": "fra",
  "Deutsch": "deu",
  "Português": "por",
  "Italiano": "ita",
};
