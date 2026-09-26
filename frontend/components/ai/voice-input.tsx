"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  lang?: string;
  /** Increment to start recording remotely (global mic button). */
  startSignal?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

function getToken(): string | null {
  try {
    const raw = localStorage.getItem("croppilot-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.state?.token ?? parsed?.token ?? null;
  } catch {
    return null;
  }
}

function floatToPcm16Base64(input: Float32Array): string {
  const out = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  const bytes = new Uint8Array(out.buffer);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000) as unknown as number[]);
  }
  return btoa(bin);
}

export function VoiceInput({ onTranscript, disabled, lang = "te", startSignal }: VoiceInputProps) {
  const { t } = useTranslation();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<{ ctx: AudioContext; stream: MediaStream; proc: ScriptProcessorNode } | null>(null);
  const audioOutRef = useRef<AudioContext | null>(null);

  const showNotice = (text: string) => {
    setNotice(text);
    setTimeout(() => setNotice(null), 3500);
  };

  const teardown = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    const a = audioRef.current;
    if (a) {
      a.proc.disconnect();
      a.ctx.close().catch(() => {});
      a.stream.getTracks().forEach((t) => t.stop());
      audioRef.current = null;
    }
  }, []);

  useEffect(() => teardown, [teardown]);

  const playAudio = useCallback(async (base64Parts: string[]) => {
    try {
      const bin = atob(base64Parts.join(""));
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const ctx = audioOutRef.current ?? new AudioContext();
      audioOutRef.current = ctx;
      const buf = await ctx.decodeAudioData(bytes.buffer.slice(0));
      const src = ctx.createBufferSource();
      src.connect(ctx.destination);
      setIsPlaying(true);
      src.onended = () => setIsPlaying(false);
      src.start();
    } catch {
      setIsPlaying(false);
    }
  }, []);

  const startRecording = async () => {
    try {
      setNotice(null);
      const token = getToken();
      const ws = new WebSocket(
        `${WS_BASE}/ws/voice?lang=${encodeURIComponent(lang)}${token ? `&token=${encodeURIComponent(token)}` : ""}`
      );
      wsRef.current = ws;
      const audioParts: string[] = [];
      let gotFinal = false;

      ws.onmessage = (ev) => {
        let msg: { type: string; text?: string; data?: string; message?: string; code?: string };
        try {
          msg = JSON.parse(ev.data);
        } catch {
          return;
        }
        if (msg.type === "final" && msg.text) {
          gotFinal = true;
          onTranscript(msg.text);
        } else if (msg.type === "response" && msg.text && !gotFinal) {
          onTranscript(msg.text);
        } else if (msg.type === "audio" && msg.data) {
          audioParts.push(msg.data);
        } else if (msg.type === "audio_end") {
          setIsProcessing(false);
          if (audioParts.length > 0) void playAudio(audioParts.splice(0));
        } else if (msg.type === "error") {
          showNotice(msg.message || msg.code || t("assistant.voiceError"));
          if (msg.code === "asr_unavailable" || msg.code === "voice_disabled") {
            setIsProcessing(false);
            setIsRecording(false);
            teardown();
          }
        }
      };
      ws.onerror = () => showNotice(t("assistant.voiceUnreachable"));
      ws.onclose = () => {
        setIsRecording(false);
        setIsProcessing(false);
      };

      await new Promise<void>((resolve, reject) => {
        ws.onopen = () => resolve();
        ws.onerror = () => reject(new Error("ws"));
        setTimeout(() => reject(new Error("timeout")), 8000);
      });
      ws.send(JSON.stringify({ type: "config", lang, persist_audio: false }));

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      const src = ctx.createMediaStreamSource(stream);
      const proc = ctx.createScriptProcessor(4096, 1, 1);
      proc.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const inData = e.inputBuffer.getChannelData(0);
        const ratio = e.inputBuffer.sampleRate / 16000;
        const len = Math.floor(inData.length / ratio);
        const down = new Float32Array(len);
        for (let i = 0; i < len; i++) down[i] = inData[Math.floor(i * ratio)];
        const b64 = floatToPcm16Base64(down);
        // Server cap is ~4096 base64 chars per frame; 16 kHz mono slices fit.
        for (let i = 0; i < b64.length; i += 4000) {
          ws.send(JSON.stringify({ type: "audio", data: b64.slice(i, i + 4000), sample_rate: 16000 }));
        }
      };
      src.connect(proc);
      proc.connect(ctx.destination);
      audioRef.current = { ctx, stream, proc };
      setIsRecording(true);
    } catch {
      teardown();
      showNotice(t("assistant.micDenied"));
    }
  };

  // Global mic button: remote start via incrementing signal. Placed
  // after startRecording so the ref never captures an uninitialized fn.
  const startRef = useRef(startRecording);
  startRef.current = startRecording;
  const lastSignal = useRef(startSignal);
  useEffect(() => {
    if (startSignal && startSignal !== lastSignal.current) {
      lastSignal.current = startSignal;
      if (!disabled) void startRef.current();
    }
  }, [startSignal, disabled]);

  const stopAndCommit = () => {
    const a = audioRef.current;
    if (a) {
      a.proc.disconnect();
      a.ctx.close().catch(() => {});
      a.stream.getTracks().forEach((t) => t.stop());
      audioRef.current = null;
    }
    setIsRecording(false);
    setIsProcessing(true);
    wsRef.current?.send(JSON.stringify({ type: "commit" }));
  };

  const stopPlayback = () => {
    wsRef.current?.send(JSON.stringify({ type: "stop" }));
    setIsPlaying(false);
    teardown();
    setIsProcessing(false);
  };

  const toggle = () => {
    if (disabled || isProcessing) return;
    if (isPlaying) {
      stopPlayback();
      return;
    }
    if (isRecording) stopAndCommit();
    else void startRecording();
  };

  return (
    <div className="relative">
      <button
        onClick={toggle}
        disabled={disabled || isProcessing}
        className={cn(
          "relative flex h-9 w-9 items-center justify-center rounded-full transition-all duration-300",
          isRecording
            ? "bg-destructive text-destructive-foreground shadow-lg shadow-destructive/25"
            : "text-muted-foreground hover:text-foreground hover:bg-accent",
          disabled && "opacity-50 cursor-not-allowed",
          isProcessing && "pointer-events-none"
        )}
        title={
          isPlaying
            ? "Stop playback"
            : isRecording
              ? "Stop recording"
              : notice ?? "Voice input"
        }
      >
        <AnimatePresence mode="wait">
          {isProcessing ? (
            <motion.div
              key="processing"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <Loader2 className="h-4 w-4 animate-spin" />
            </motion.div>
          ) : isPlaying ? (
            <motion.div
              key="playing"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <Square className="h-4 w-4" />
            </motion.div>
          ) : isRecording ? (
            <motion.div
              key="recording"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <MicOff className="h-4 w-4" />
            </motion.div>
          ) : (
            <motion.div
              key="mic"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <Mic className="h-4 w-4" />
            </motion.div>
          )}
        </AnimatePresence>
      </button>

      {isRecording && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          className="absolute bottom-full start-1/2 -translate-x-1/2 mb-3"
        >
          <div className="flex items-center gap-2 rounded-full bg-destructive/10 border border-destructive/20 px-4 py-2 shadow-lg backdrop-blur-sm">
            <motion.span
              className="h-2 w-2 rounded-full bg-destructive"
              animate={{ scale: [1, 1.4, 1] }}
              transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
            />
            <span className="text-xs font-medium text-destructive whitespace-nowrap">{t("voice.recording")}</span>
            <div className="flex items-end gap-0.5 h-4 ms-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <motion.span
                  key={i}
                  className="w-0.5 rounded-full bg-destructive"
                  animate={{
                    height: [4, 12 + Math.random() * 10, 4],
                  }}
                  transition={{
                    duration: 0.5 + Math.random() * 0.3,
                    repeat: Infinity,
                    delay: i * 0.1,
                    ease: "easeInOut",
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {notice && !isRecording && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          className="absolute bottom-full start-1/2 -translate-x-1/2 mb-3"
        >
          <div className="whitespace-nowrap rounded-full bg-destructive/10 border border-destructive/20 px-3 py-1.5 text-xs text-destructive shadow-lg backdrop-blur-sm">
            {notice}
          </div>
        </motion.div>
      )}
    </div>
  );
}
