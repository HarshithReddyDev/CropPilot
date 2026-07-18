"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ChatMessage } from "@/types";
import { ChatMessage as ChatMessageComponent } from "./chat-message";

interface ChatMessagesProps {
  messages: ChatMessage[];
  isGenerating: boolean;
}

export function ChatMessages({ messages, isGenerating }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isGenerating]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6 space-y-5 scrollbar-thin"
    >
      <AnimatePresence mode="popLayout">
        {messages.map((message) => (
          <div key={message.id} className="group">
            <ChatMessageComponent message={message} />
          </div>
        ))}
      </AnimatePresence>

      {isGenerating && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          className="flex items-start gap-3"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2a4 4 0 014 4c0 2-2 4-4 4s-4-2-4-4 2-4 4-4z" />
              <path d="M2 22v-1a6 6 0 0112 0v1" />
              <path d="M22 22v-1a6 6 0 00-6-6" />
            </svg>
          </div>
          <div className="glass-card rounded-2xl rounded-bl-md px-4 py-3">
            <TypingIndicator />
          </div>
        </motion.div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-2 w-2 rounded-full bg-primary/60"
          animate={{
            y: [0, -4, 0],
            opacity: [0.4, 1, 0.4],
          }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.15,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
