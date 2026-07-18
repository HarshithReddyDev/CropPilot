"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileImage, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface DragDropUploadProps {
  onFile: (file: File, preview: string) => void;
  disabled?: boolean;
}

export function DragDropUpload({ onFile, disabled }: DragDropUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndProcess = useCallback(
    (file: File) => {
      setError(null);

      if (!file.type.startsWith("image/")) {
        setError("Please select an image file.");
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        setError("File size must be under 10MB.");
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        setPreview(dataUrl);
        setFileName(file.name);
        onFile(file, dataUrl);
      };
      reader.readAsDataURL(file);
    },
    [onFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) validateAndProcess(file);
    },
    [validateAndProcess]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndProcess(file);
    },
    [validateAndProcess]
  );

  const handleRemove = useCallback(() => {
    setPreview(null);
    setFileName(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-border/50 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Upload className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Upload Image</h3>
          <p className="text-xs text-muted-foreground">Drag & drop or browse</p>
        </div>
      </div>

      <div className="p-5">
        <AnimatePresence mode="wait">
          {!preview ? (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !disabled && inputRef.current?.click()}
              className={cn(
                "relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-all",
                isDragging
                  ? "border-primary bg-primary/5 scale-[1.02]"
                  : "border-muted-foreground/25 hover:border-muted-foreground/50 hover:bg-muted/30",
                disabled && "cursor-not-allowed opacity-50"
              )}
            >
              <motion.div
                animate={isDragging ? { y: -8, scale: 1.1 } : {}}
                className="flex h-14 w-14 items-center justify-center rounded-full bg-muted"
              >
                <FileImage className="h-6 w-6 text-muted-foreground" />
              </motion.div>
              <div className="text-center">
                <p className="text-sm font-medium text-foreground">
                  Drag & drop or click to upload
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  JPG, PNG, WEBP up to 10MB
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className="group relative overflow-hidden rounded-xl bg-muted">
                <img
                  src={preview}
                  alt={fileName ?? "Uploaded"}
                  className="h-48 w-full object-cover"
                />
                <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/20" />
                <button
                  onClick={handleRemove}
                  className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/50 text-white opacity-0 transition-opacity hover:bg-black/70 group-hover:opacity-100"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              {fileName && (
                <p className="truncate text-xs text-muted-foreground">{fileName}</p>
              )}
              <button
                onClick={() => inputRef.current?.click()}
                className="w-full rounded-lg border border-border py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted"
              >
                Change Image
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 flex items-center gap-2 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-500"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </motion.div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
    </div>
  );
}
