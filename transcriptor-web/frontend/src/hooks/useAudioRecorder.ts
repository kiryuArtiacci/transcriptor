import { useRef, useState, useCallback } from "react";

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timerRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  const start = useCallback(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      chunks.current = [];
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      recorder.start(5000);
      mediaRecorder.current = recorder;
      setIsRecording(true);
      setIsPaused(false);
      startTimeRef.current = Date.now();
      timerRef.current = window.setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 1000);
    });
  }, []);

  const pause = useCallback(() => {
    if (!mediaRecorder.current || mediaRecorder.current.state !== "recording")
      return;
    mediaRecorder.current.pause();
    clearInterval(timerRef.current);
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
    return new Promise((resolve) => {
      if (!mediaRecorder.current) return;
      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        resolve(blob);
      };
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach((t) => t.stop());
      clearInterval(timerRef.current);
      setIsRecording(false);
      setIsPaused(false);
      setElapsed(0);
    });
  }, []);

  return { isRecording, isPaused, elapsed, start, pause, resume, stop };
}
