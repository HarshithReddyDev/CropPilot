"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  ChevronRight,
  User,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatTime } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";
import { MarkdownRenderer } from "./markdown-renderer";

interface ChatMessageProps {
  message: ChatMessageType;
  isTyping?: boolean;
}

export function ChatMessage({ message, isTyping }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary mt-1">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div className={cn("flex max-w-[85%] sm:max-w-[75%] flex-col", isUser && "items-end")}>
        <div
          className={cn(
            "relative rounded-2xl px-4 py-3",
            isUser
              ? "bg-primary text-primary-foreground rounded-br-md"
              : "glass-card rounded-bl-md"
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        <div
          className={cn(
            "mt-1 flex items-center gap-2 px-1",
            isUser ? "flex-row-reverse" : "flex-row"
          )}
        >
          <span className="text-[10px] text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>

          {!isUser && (
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="flex h-6 w-6 items-center justify-center rounded hover:bg-accent transition-colors"
                title="Copy response"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-primary" />
                ) : (
                  <Copy className="h-3 w-3 text-muted-foreground" />
                )}
              </button>
              <button
                onClick={() => setFeedback(feedback === "up" ? null : "up")}
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded hover:bg-accent transition-colors",
                  feedback === "up" && "text-primary"
                )}
                title="Helpful"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>
              <button
                onClick={() => setFeedback(feedback === "down" ? null : "down")}
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded hover:bg-accent transition-colors",
                  feedback === "down" && "text-destructive"
                )}
                title="Not helpful"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>
            </div>
          )}

          {isUser && (
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20">
              <User className="h-3 w-3 text-primary" />
            </div>
          )}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            >
              {sourcesOpen ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {message.sources.length} source{message.sources.length > 1 ? "s" : ""}
            </button>
            {sourcesOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-1 space-y-1.5 pl-3"
              >
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-border bg-card/50 px-3 py-2 text-xs"
                  >
                    <p className="font-medium text-foreground">{source.title}</p>
                    <p className="mt-0.5 text-muted-foreground line-clamp-2">
                      {source.content}
                    </p>
                    {source.score !== undefined && (
                      <div className="mt-1 flex items-center gap-1">
                        <div className="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${Math.round(source.score * 100)}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-muted-foreground">
                          {Math.round(source.score * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </motion.div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground mt-1">
          <User className="h-4 w-4" />
        </div>
      )}
    </motion.div>
  );
}
