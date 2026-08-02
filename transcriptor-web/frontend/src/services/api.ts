import axios from "axios";
import { OcrResult, TranscriptionResult } from "../types";

const API = axios.create({ baseURL: "/api" });

export async function transcribeFile(
  file: File,
  language: string,
  diarize: boolean
): Promise<TranscriptionResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("language", language);
  form.append("diarize", String(diarize));
  const res = await API.post<TranscriptionResult>("/transcribe/file", form);
  return res.data;
}

export async function transcribeLive(
  file: Blob,
  filename: string,
  language: string,
  diarize: boolean
): Promise<TranscriptionResult> {
  const form = new FormData();
  form.append("file", file, filename);
  form.append("language", language);
  form.append("diarize", String(diarize));
  const res = await API.post<TranscriptionResult>("/transcribe/live", form);
  return res.data;
}

export async function extractOcr(
  file: File,
  language: string
): Promise<OcrResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("language", language);
  const res = await API.post<OcrResult>("/ocr", form);
  return res.data;
}
