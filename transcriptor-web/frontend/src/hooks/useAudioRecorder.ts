import { useRef, useState, useCallback } from "react";

function pickMimeType(): string {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  if (typeof MediaRecorder !== "undefined") {
    for (const t of candidates) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
  }
  return "";
}

export function extensionFromMimeType(mimeType: string): string {
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("ogg")) return "ogg";
  return "webm";
}

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mimeTypeRef = useRef<string>("");
  const chunks = useRef<Blob[]>([]);
  const timerRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  const clearTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = 0;
    }
  };

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunks.current = [];

      const mimeType = pickMimeType();
      mimeTypeRef.current = mimeType;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      recorder.start(1000);
      mediaRecorder.current = recorder;
      setIsRecording(true);
      setIsPaused(false);
      setElapsed(0);
      startTimeRef.current = Date.now();
      timerRef.current = window.setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 1000);
    } catch (e) {
      const msg =
        e instanceof DOMException && e.name === "NotAllowedError"
          ? "Permiso de micrófono denegado. Permití el acceso en tu navegador."
          : e instanceof DOMException && e.name === "NotFoundError"
          ? "No se encontró ningún micrófono."
          : String(e);
      setError("No se pudo acceder al micrófono: " + msg);
    }
  }, []);

  const pause = useCallback(() => {
    if (!mediaRecorder.current || mediaRecorder.current.state !== "recording")
      return;
    mediaRecorder.current.pause();
    clearTimer();
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    if (!mediaRecorder.current || mediaRecorder.current.state !== "paused") return;
    mediaRecorder.current.resume();
    startTimeRef.current = Date.now() - elapsed * 1000;
    timerRef.current = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    setIsPaused(false);
  }, [elapsed]);

  const stop = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorder.current;
      if (!recorder || recorder.state === "inactive") {
        reject(new Error("No hay grabación en curso."));
        return;
      }
      recorder.onstop = () => {
        const blob = new Blob(chunks.current, {
          type: mimeTypeRef.current || "audio/webm",
        });
        resolve(blob);
      };
      recorder.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      clearTimer();
      setIsRecording(false);
      setIsPaused(false);
      setElapsed(0);
    });
  }, []);

  return { isRecording, isPaused, elapsed, error, start, pause, resume, stop };
}
