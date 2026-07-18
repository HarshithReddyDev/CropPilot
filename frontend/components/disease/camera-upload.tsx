"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, CameraOff, Image, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useMediaDevices } from "@/hooks/use-media-devices";

interface CameraUploadProps {
  onCapture: (imageData: string) => void;
  disabled?: boolean;
}

export function CameraUpload({ onCapture, disabled }: CameraUploadProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [capturedPreview, setCapturedPreview] = useState<string | null>(null);

  const { stream, error, isStreaming, startCamera, stopCamera, captureFrame } =
    useMediaDevices();

  useEffect(() => {
    if (isStreaming && videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [isStreaming, stream]);

  const handleToggleCamera = useCallback(async () => {
    if (showCamera) {
      stopCamera();
      setShowCamera(false);
      setCapturedPreview(null);
    } else {
      await startCamera();
      setShowCamera(true);
    }
  }, [showCamera, startCamera, stopCamera]);

  const handleCapture = useCallback(() => {
    const frame = captureFrame();
    if (frame) {
      setCapturedPreview(frame);
      onCapture(frame);
      stopCamera();
      setShowCamera(false);
    }
  }, [captureFrame, onCapture, stopCamera]);

  const handleRetake = useCallback(() => {
    setCapturedPreview(null);
    startCamera();
    setShowCamera(true);
  }, [startCamera]);

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-border/50 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Camera className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-foreground">Camera Capture</h3>
          <p className="text-xs text-muted-foreground">Take a photo of the affected crop</p>
        </div>
        {isStreaming && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="flex items-center gap-1.5 rounded-full bg-red-500/10 px-2.5 py-1 text-[10px] font-medium text-red-500"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
            </span>
            LIVE
          </motion.span>
        )}
      </div>

      <div className="p-5">
        <AnimatePresence mode="wait">
          {!showCamera && !capturedPreview ? (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4 py-6"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <Camera className="h-7 w-7 text-muted-foreground" />
              </div>
              <p className="text-center text-sm text-muted-foreground">
                Position the affected leaves or fruits in frame
              </p>
              <Button
                onClick={handleToggleCamera}
                disabled={disabled}
                className="gap-2"
              >
                <Camera className="h-4 w-4" />
                Activate Camera
              </Button>
            </motion.div>
          ) : showCamera && !capturedPreview ? (
            <motion.div
              key="camera"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="space-y-4"
            >
              <div className="relative overflow-hidden rounded-xl bg-black aspect-[4/3]">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="h-full w-full object-cover"
                />
                {error && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/60 p-4">
                    <p className="text-center text-sm text-white">{error}</p>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleToggleCamera}
                  className="flex-1 gap-2"
                >
                  <CameraOff className="h-4 w-4" />
                  Cancel
                </Button>
                <Button
                  onClick={handleCapture}
                  disabled={!!error}
                  className="flex-1 gap-2"
                >
                  <Camera className="h-4 w-4" />
                  Capture
                </Button>
              </div>
            </motion.div>
          ) : capturedPreview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="relative overflow-hidden rounded-xl bg-black aspect-[4/3]">
                <img
                  src={capturedPreview}
                  alt="Captured"
                  className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 ring-1 ring-inset ring-white/10" />
              </div>
              <Button
                variant="outline"
                onClick={handleRetake}
                className="w-full gap-2"
              >
                <Camera className="h-4 w-4" />
                Retake
              </Button>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  );
}
