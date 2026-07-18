"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  MessageSquare,
  Trash2,
  CalendarDays,
  MessageCircle,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { cn, formatDate, truncate } from "@/lib/utils";

interface Conversation {
  id: string;
  title: string;
  preview: string;
  date: string;
  messageCount: number;
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  isCollapsed,
  onToggleCollapse,
}: ConversationSidebarProps) {
  const [search, setSearch] = useState("");

  const filtered = search.trim()
    ? conversations.filter(
        (c) =>
          c.title.toLowerCase().includes(search.toLowerCase()) ||
          c.preview.toLowerCase().includes(search.toLowerCase())
      )
    : conversations;

  return (
    <motion.aside
      animate={{ width: isCollapsed ? 0 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className={cn(
        "relative flex flex-col border-r border-border bg-card overflow-hidden",
        isCollapsed ? "min-w-0" : "min-w-[280px]"
      )}
    >
      <div className={cn("flex flex-col h-full", isCollapsed && "invisible")}>
        <div className="flex items-center justify-between p-3 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Conversations</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={onToggleCollapse}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Close sidebar"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="p-3">
          <button
            onClick={onNew}
            className="flex w-full items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90 active:scale-[0.98]"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        <div className="px-3 pb-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50 transition-colors"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1 scrollbar-thin">
          <AnimatePresence mode="popLayout">
            {filtered.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center gap-2 py-8 text-center"
              >
                <MessageSquare className="h-8 w-8 text-muted-foreground/40" />
                <p className="text-xs text-muted-foreground">
                  {search ? "No conversations found" : "No conversations yet"}
                </p>
              </motion.div>
            ) : (
              filtered.map((conv) => (
                <motion.div
                  key={conv.id}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="group relative"
                >
                  <button
                    onClick={() => onSelect(conv.id)}
                    className={cn(
                      "w-full rounded-xl px-3 py-2.5 text-left transition-all",
                      activeId === conv.id
                        ? "bg-primary/10 border border-primary/20"
                        : "hover:bg-accent border border-transparent"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-foreground truncate">
                          {conv.title}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground line-clamp-1">
                          {conv.preview}
                        </p>
                      </div>
                    </div>
                    <div className="mt-1.5 flex items-center gap-3 text-[10px] text-muted-foreground/60">
                      <span className="flex items-center gap-1">
                        <CalendarDays className="h-3 w-3" />
                        {formatDate(conv.date)}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageCircle className="h-3 w-3" />
                        {conv.messageCount}
                      </span>
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(conv.id);
                    }}
                    className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-lg opacity-0 group-hover:opacity-100 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                    title="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>

      {isCollapsed && (
        <button
          onClick={onToggleCollapse}
          className="absolute inset-y-0 right-0 z-10 flex items-center justify-center w-8 bg-card/50 backdrop-blur-sm border-l border-border opacity-0 hover:opacity-100 transition-opacity"
          title="Open sidebar"
        >
          <PanelLeft className="h-4 w-4 text-muted-foreground" />
        </button>
      )}
    </motion.aside>
  );
}
