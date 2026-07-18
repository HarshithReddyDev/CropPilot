"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Paperclip, X, FileText, Image, Camera, Upload, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "application/pdf",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

interface FilePreview {
  file: File;
  id: string;
  previewUrl?: string;
  uploadProgress: number;
  error?: string;
}

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export function FileUpload({ onFilesSelected, disabled }: FileUploadProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [files, setFiles] = useState<FilePreview[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" exceeds 10MB limit`;
    }
    if (!ACCEPTED_TYPES.includes(file.type) && !file.type.startsWith("image/")) {
      return `File type "${file.type || "unknown"}" is not supported`;
    }
    return null;
  };

  const processFiles = useCallback(
    (selectedFiles: FileList | File[]) => {
      const newFiles: FilePreview[] = [];
      const validFiles: File[] = [];

      Array.from(selectedFiles).forEach((file) => {
        const error = validateFile(file);
        const preview: FilePreview = {
          file,
          id: crypto.randomUUID(),
          uploadProgress: 0,
          error: error || undefined,
        };
        if (file.type.startsWith("image/") && !error) {
          preview.previewUrl = URL.createObjectURL(file);
        }
        newFiles.push(preview);
        if (!error) validFiles.push(file);
      });

      setFiles((prev) => [...prev, ...newFiles]);
      if (validFiles.length > 0) {
        setIsUploading(true);
        validFiles.forEach((_, idx) => {
          const fileIdx = files.length + idx;
          const interval = setInterval(() => {
            setFiles((prev) => {
              const updated = [...prev];
              if (updated[fileIdx]) {
                updated[fileIdx] = {
                  ...updated[fileIdx],
                  uploadProgress: Math.min(updated[fileIdx].uploadProgress + 25, 100),
                };
              }
              return updated;
            });
          }, 150);
          setTimeout(() => {
            clearInterval(interval);
            if (idx === validFiles.length - 1) {
              setTimeout(() => {
                setIsUploading(false);
                onFilesSelected(validFiles);
              }, 300);
            }
          }, 1000);
        });
      }
    },
    [files.length, onFilesSelected]
  );

  const removeFile = (id: string) => {
    setFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.previewUrl) URL.revokeObjectURL(file.previewUrl);
      return prev.filter((f) => f.id !== id);
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      e.target.value = "";
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt"
        className="hidden"
        onChange={handleFileSelect}
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileSelect}
      />

      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled || isUploading}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-full transition-colors",
            "text-muted-foreground hover:text-foreground hover:bg-accent",
            (disabled || isUploading) && "opacity-50 cursor-not-allowed"
          )}
          title="Attach files"
        >
          <Paperclip className="h-4 w-4" />
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-full left-0 mb-2 w-48 rounded-xl border border-border bg-card shadow-xl backdrop-blur-xl overflow-hidden"
            >
              <div className="p-1.5">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm hover:bg-accent transition-colors"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Image className="h-4 w-4" />
                  </div>
                  <span className="font-medium">Images & Documents</span>
                </button>
                <button
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm hover:bg-accent transition-colors"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                    <Camera className="h-4 w-4" />
                  </div>
                  <span className="font-medium">Take a Photo</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="flex flex-wrap gap-2 mb-2"
          >
            {files.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className={cn(
                  "group relative flex items-center gap-2 rounded-lg border px-3 py-2 text-sm",
                  file.error
                    ? "border-destructive/50 bg-destructive/5"
                    : "border-border bg-card"
                )}
              >
                {file.file.type.startsWith("image/") && file.previewUrl ? (
                  <div className="h-8 w-8 rounded-md overflow-hidden flex-shrink-0">
                    <img
                      src={file.previewUrl}
                      alt={file.file.name}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted flex-shrink-0">
                    {file.file.type === "application/pdf" ? (
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate text-foreground">
                    {file.file.name}
                  </p>
                  {file.error ? (
                    <p className="text-xs text-destructive flex items-center gap-1 mt-0.5">
                      <AlertCircle className="h-3 w-3" />
                      {file.error}
                    </p>
                  ) : file.uploadProgress < 100 ? (
                    <div className="flex items-center gap-2 mt-1">
                      <div className="h-1 flex-1 rounded-full bg-muted overflow-hidden">
                        <motion.div
                          className="h-full rounded-full bg-primary"
                          initial={{ width: 0 }}
                          animate={{ width: `${file.uploadProgress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      <span className="text-[10px] text-muted-foreground">
                        {file.uploadProgress}%
                      </span>
                    </div>
                  ) : (
                    <p className="text-[10px] text-primary flex items-center gap-1 mt-0.5">
                      <Upload className="h-3 w-3" />
                      Uploaded
                    </p>
                  )}
                </div>
                <button
                  onClick={() => removeFile(file.id)}
                  className="flex h-5 w-5 items-center justify-center rounded-full opacity-0 group-hover:opacity-100 hover:bg-muted transition-all"
                >
                  <X className="h-3 w-3 text-muted-foreground" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
