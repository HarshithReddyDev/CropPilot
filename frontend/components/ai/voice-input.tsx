"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const cleanup = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }, []);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  const startRecording = async () => {
    try {
      setPermissionDenied(false);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setIsProcessing(true);
        await new Promise((resolve) => setTimeout(resolve, 1200));
        const mockTranscripts = [
          "What are the best practices for wheat cultivation in Punjab?",
          "Show me the latest market prices for rice in my area",
          "How do I treat leaf blight in tomato plants?",
          "What government schemes am I eligible for as a small farmer?",
        ];
        const transcript = mockTranscripts[Math.floor(Math.random() * mockTranscripts.length)];
        onTranscript(transcript);
        setIsProcessing(false);
      };

      recorder.start();
      setIsRecording(true);
    } catch {
      setPermissionDenied(true);
      setTimeout(() => setPermissionDenied(false), 3000);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const toggle = () => {
    if (disabled) return;
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
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
        title={isRecording ? "Stop recording" : permissionDenied ? "Microphone access denied" : "Voice input"}
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
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3"
        >
          <div className="flex items-center gap-2 rounded-full bg-destructive/10 border border-destructive/20 px-4 py-2 shadow-lg backdrop-blur-sm">
            <motion.span
              className="h-2 w-2 rounded-full bg-destructive"
              animate={{ scale: [1, 1.4, 1] }}
              transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
            />
            <span className="text-xs font-medium text-destructive whitespace-nowrap">Recording...</span>
            <div className="flex items-end gap-0.5 h-4 ml-2">
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

      {permissionDenied && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3"
        >
          <div className="whitespace-nowrap rounded-full bg-destructive/10 border border-destructive/20 px-3 py-1.5 text-xs text-destructive shadow-lg backdrop-blur-sm">
            Microphone access denied
          </div>
        </motion.div>
      )}
    </div>
  );
}
