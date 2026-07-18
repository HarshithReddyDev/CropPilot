"use client";

import { useState, useRef, useCallback, useEffect, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { FileUpload } from "./file-upload";
import { VoiceInput } from "./voice-input";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  suggestedPrompts?: string[];
}

export function ChatInput({
  onSend,
  disabled,
  placeholder = "Ask about crops, diseases, markets, schemes...",
  suggestedPrompts,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [input, adjustHeight]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (files: File[]) => {
    const fileMsg = files
      .map((f) => `[Attached: ${f.name}]`)
      .join("\n");
    if (fileMsg) {
      setInput((prev) => (prev ? `${prev}\n${fileMsg}` : fileMsg));
    }
  };

  const handleVoiceTranscript = (text: string) => {
    setInput((prev) => (prev ? `${prev} ${text}` : text));
  };

  return (
    <div className="border-t border-border bg-background/95 backdrop-blur-xl">
      <AnimatePresence>
        {suggestedPrompts && suggestedPrompts.length > 0 && input.length === 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex gap-2 overflow-x-auto px-4 pt-3 pb-2 scrollbar-hide"
          >
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => onSend(prompt)}
                className="flex-shrink-0 rounded-full border border-border bg-card/50 px-3 py-1.5 text-xs text-muted-foreground hover:border-primary/30 hover:text-foreground hover:bg-card transition-all whitespace-nowrap"
              >
                {prompt}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-end gap-2 px-4 py-3">
        <FileUpload onFilesSelected={handleFileSelect} disabled={disabled} />

        <div
          className={cn(
            "relative flex-1 flex items-end rounded-2xl border bg-card transition-all duration-200",
            isFocused
              ? "border-primary/50 shadow-lg shadow-primary/5"
              : "border-border hover:border-primary/30"
          )}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none max-h-[200px] scrollbar-thin"
          />
          <div className="flex items-center gap-1 pr-2 pb-2">
            <VoiceInput onTranscript={handleVoiceTranscript} disabled={disabled} />
          </div>
        </div>

        <motion.button
          whileHover={{ scale: input.trim() && !disabled ? 1.05 : 1 }}
          whileTap={{ scale: input.trim() && !disabled ? 0.95 : 1 }}
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all duration-200",
            input.trim() && !disabled
              ? "bg-primary text-primary-foreground shadow-lg shadow-primary/25 hover:bg-primary/90"
              : "bg-muted text-muted-foreground cursor-not-allowed"
          )}
        >
          {input.trim() ? (
            <Send className="h-4 w-4" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
        </motion.button>
      </div>

      <p className="pb-2 text-center text-[10px] text-muted-foreground/50">
        Enter to send &middot; Shift + Enter for new line
      </p>
    </div>
  );
}
