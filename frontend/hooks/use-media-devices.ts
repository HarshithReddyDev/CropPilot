"use client";

import { useState, useRef, useCallback } from "react";

interface UseMediaDevicesReturn {
  stream: MediaStream | null;
  error: string | null;
  isStreaming: boolean;
  startCamera: (constraints?: MediaStreamConstraints) => Promise<void>;
  stopCamera: () => void;
  captureFrame: () => string | null;
}

export function useMediaDevices(): UseMediaDevicesReturn {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const startCamera = useCallback(
    async (constraints?: MediaStreamConstraints) => {
      setError(null);
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error(
            "Camera access is not supported in this browser."
          );
        }

        const mediaStream = await navigator.mediaDevices.getUserMedia(
          constraints ?? {
            video: {
              facingMode: "environment",
              width: { ideal: 1280 },
              height: { ideal: 720 },
            },
            audio: false,
          }
        );

        streamRef.current = mediaStream;
        setStream(mediaStream);
        setIsStreaming(true);

        const video = document.createElement("video");
        video.srcObject = mediaStream;
        video.setAttribute("playsinline", "");
        videoRef.current = video;
        await video.play();
      } catch (err) {
        let message = "Failed to access camera.";
        if (err instanceof DOMException) {
          switch (err.name) {
            case "NotAllowedError":
              message =
                "Camera access denied. Please allow camera permissions.";
              break;
            case "NotFoundError":
              message = "No camera found on this device.";
              break;
            case "NotReadableError":
              message =
                "Camera is already in use by another application.";
              break;
            case "OverconstrainedError":
              message = "Camera constraints could not be satisfied.";
              break;
          }
        } else if (err instanceof Error) {
          message = err.message;
        }
        setError(message);
        setIsStreaming(false);
      }
    },
    []
  );

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
      videoRef.current = null;
    }
    setStream(null);
    setIsStreaming(false);
    setError(null);
  }, []);

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || !streamRef.current) return null;

    try {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL("image/jpeg", 0.9);
    } catch {
      return null;
    }
  }, []);

  return {
    stream,
    error,
    isStreaming,
    startCamera,
    stopCamera,
    captureFrame,
  };
}
