"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Bot, Sparkles } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { ChatMessages } from "@/components/ai/chat-messages";
import { ChatInput } from "@/components/ai/chat-input";
import { ConversationSidebar } from "@/components/ai/conversation-sidebar";
import { SuggestedPrompts } from "@/components/ai/suggested-prompts";
import type { ChatMessage, Source } from "@/types";
import { generateId } from "@/lib/utils";
import { useLocaleStore } from "@/stores/locale-store";
import { useTranslation } from "@/lib/i18n";
import {
  postChat,
  streamChat,
  pageContext,
  takeMapAssistantContext,
  type AssistantReply,
  type AssistantUIAction,
} from "@/services/assistant";

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "",
  timestamp: new Date().toISOString(),
};

function welcomeContent(t: (key: string) => string): string {
  // Catalog holds the full localized welcome; empty means a locale that
  // fell back before catalogs loaded — use English inline as last resort.
  return t("assistant.welcome") === "assistant.welcome"
    ? "Hello! I'm **CropPilot AI**."
    : t("assistant.welcome");
}




interface Conversation {
  id: string;
  title: string;
  preview: string;
  date: string;
  messageCount: number;
}

const THREAD_STORE_KEY = "croppilot-assistant-threads-v1";

interface ThreadStore {
  threads: Record<string, ChatMessage[]>;
  serverIds: Record<string, string>;
  conversations: Conversation[];
  active: string;
}

function loadThreadStore(): ThreadStore | null {
  try {
    const raw = localStorage.getItem(THREAD_STORE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ThreadStore>;
    if (!parsed || typeof parsed !== "object" || !parsed.threads) return null;
    return {
      threads: parsed.threads as Record<string, ChatMessage[]>,
      serverIds: (parsed.serverIds ?? {}) as Record<string, string>,
      conversations: (parsed.conversations ?? []) as Conversation[],
      active: typeof parsed.active === "string" ? parsed.active : "conv-default",
    };
  } catch {
    return null;
  }
}

export default function AiAssistantPage() {
  const { t } = useTranslation();
  const welcome = useMemo(
    () => ({ ...WELCOME_MESSAGE, content: welcomeContent(t) }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t]
  );
  const [store] = useState<ThreadStore | null>(() =>
    typeof window === "undefined" ? null : loadThreadStore()
  );
  const [messages, setMessages] = useState<ChatMessage[]>(
    () =>
      (store && store.threads[store.active]) || [welcome]
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>(
    () =>
      (store && store.conversations.length && store.conversations) || [
        {
          id: "conv-default",
          title: t("assistant.welcomeTitle"),
          preview: t("assistant.welcomePreview"),
          date: new Date().toISOString(),
          messageCount: 1,
        },
      ]
  );
  const [activeConversation, setActiveConversation] = useState<string>(
    () => (store && store.threads[store.active] && store.active) || "conv-default"
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const abortRef = useRef<(() => void) | null>(null);
  const threadsRef = useRef<Record<string, ChatMessage[]>>(
    (store && store.threads) || {
      "conv-default": [welcome],
    }
  );
  // Server-owned conversation ids (Phase 7 memory). Local thread keys stay
  // stable; the server id is sent once known so follow-ups share history.
  const serverIdsRef = useRef<Record<string, string>>(
    (store && store.serverIds) || {}
  );
  const router = useRouter();

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true);
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Persist the active thread on every change so switching
  // conversations (and full page reloads) restore per-conversation messages.
  useEffect(() => {
    threadsRef.current[activeConversation] = messages;
    try {
      const snapshot: ThreadStore = {
        threads: threadsRef.current,
        serverIds: serverIdsRef.current,
        conversations,
        active: activeConversation,
      };
      localStorage.setItem(THREAD_STORE_KEY, JSON.stringify(snapshot));
    } catch {
      // Storage full or unavailable: threads still work for this session.
    }
  }, [messages, conversations, activeConversation]);

  // Cross-page bridge (§23): markets/schemes/weather pages dispatch
  // `croppilot:send-chat` to push a message into the assistant.
  // Global mic (§16): header dispatches `croppilot:start-voice`, or
  // navigates here with ?voice=1; both increment the voice signal.
  const [voiceSignal, setVoiceSignal] = useState(0);
  const sendRef = useRef<(content: string) => void>(() => {});
  useEffect(() => {
    const listener = (e: Event) => {
      const text = (e as CustomEvent<string>).detail;
      if (typeof text === "string" && text.trim()) sendRef.current(text);
    };
    const voiceListener = () => setVoiceSignal((n) => n + 1);
    window.addEventListener("croppilot:send-chat", listener);
    window.addEventListener("croppilot:start-voice", voiceListener);
    const params = new URLSearchParams(window.location.search);
    if (params.get("voice") === "1") {
      window.history.replaceState({}, "", window.location.pathname);
      setVoiceSignal((n) => n + 1);
    }
    return () => {
      window.removeEventListener("croppilot:send-chat", listener);
      window.removeEventListener("croppilot:start-voice", voiceListener);
    };
  }, []);

  const applyUiActions = useCallback(
    (actions: AssistantUIAction[]) => {
      for (const a of actions ?? []) {
        const p = (a.payload ?? {}) as Record<string, unknown>;
        if (a.action === "apply-market-filters" || a.action === "open-market") {
          const q = new URLSearchParams();
          for (const k of ["state", "district", "market", "commodity", "variety", "grade"]) {
            if (typeof p[k] === "string" && (p[k] as string).trim()) q.set(k, p[k] as string);
          }
          router.push(`/markets${q.toString() ? `?${q.toString()}` : ""}`);
        } else if (a.action === "open-article") {
          // Defense in depth: backend strips off-spec keys (no url survives),
          // but never open non-http(s) targets even if malformed data arrives.
          if (typeof p.url === "string" && /^https?:\/\//i.test(p.url))
            window.open(p.url, "_blank", "noopener");
        } else if (a.action === "assistant.set_language") {
          // Store sanitizes against the canonical 23-locale registry;
          // unshipped catalogs fall back to English strings.
          if (typeof p.language === "string" && p.language.trim()) {
            useLocaleStore.getState().setLocale(p.language);
          }
        } else if (a.action === "page.read_aloud") {
          // Frontend-determined eligible content only: headings + text
          // of <main>, bounded. Explicit browser speech fallback (server
          // TTS unavailable until engines install).
          try {
            const main = document.querySelector("main");
            const text = (main?.innerText ?? "").replace(/\s+/g, " ").trim().slice(0, 2000);
            if (text && "speechSynthesis" in window) {
              window.speechSynthesis.cancel();
              window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
            }
          } catch {
            // Reading must never break the chat turn.
          }
        } else if (a.action === "navigation.open_page") {
          // Frontend-validated: internal allow-listed pages only, never URLs.
          if (typeof p.page === "string" && /^(dashboard|markets|weather|disease-detection|schemes|analytics|maps|ai-assistant)$/.test(p.page)) {
            router.push(`/${p.page}`);
          }
        }
        // follow-market / play-audio: no Phase 5 surface; action validated server-side.
      }
    },
    [router]
  );

  const createNewConversation = useCallback(() => {
    const id = generateId();
    const conv: Conversation = {
      id,
      title: t("assistant.newChatTitle"),
      preview: t("assistant.newChatPreview"),
      date: new Date().toISOString(),
      messageCount: 0,
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveConversation(id);
    setMessages([welcome]);
  }, []);

  const handleSend = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsGenerating(true);

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversation
            ? {
                ...c,
                title: c.messageCount === 0 ? content.slice(0, 50) : c.title,
                preview: content.slice(0, 60),
                date: new Date().toISOString(),
                messageCount: c.messageCount + 1,
              }
            : c
        )
      );

      const assistantId = generateId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      const patch = (content: string, sources?: Source[]) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content, ...(sources ? { sources } : {}) }
              : m
          )
        );
      };

      const finish = (reply: AssistantReply) => {
        if (reply.conversation_id) serverIdsRef.current[activeConversation] = reply.conversation_id;
        const sources: Source[] = (reply.citations ?? []).map((c) => ({
          title: c.title || c.source || "Source",
          content: c.snippet || "",
          score: c.score ?? undefined,
        }));
        patch(reply.text || "Empty response.", sources.length ? sources : undefined);
        if (reply.ui_actions?.length) applyUiActions(reply.ui_actions);
        setIsGenerating(false);
        abortRef.current = null;
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConversation
              ? { ...c, messageCount: c.messageCount + 1 }
              : c
          )
        );
      };

      const ctrl = new AbortController();
      abortRef.current = () => ctrl.abort();
      let accumulated = "";
      const serverId = serverIdsRef.current[activeConversation];
      // Page-aware context: route + UI language flow into every turn.
      // A fresh map handoff (location/layers/market) is attached once so
      // "what are the nearby markets?" works without retyping coordinates.
      const ctx = { ...pageContext(), page: "ai-assistant" };
      const mapCtx = takeMapAssistantContext();
      const ctxWithMap = mapCtx
        ? { ...ctx, page_filters: { ...(ctx.page_filters ?? {}), map: mapCtx } }
        : ctx;

      try {
        const streamed = await streamChat(content, serverId, {
          signal: ctrl.signal,
          onDelta: (d) => {
            accumulated += d;
            patch(accumulated);
          },
          onFinal: (reply) => finish(reply),
          onError: (msg) => {
            patch(msg || t("assistant.offline"));
            setIsGenerating(false);
            abortRef.current = null;
          },
        }, ctxWithMap);
        // SSE unavailable: fall back to the non-streaming turn.
        if (!streamed && !ctrl.signal.aborted) finish(await postChat(content, serverId, ctxWithMap));
      } catch (e) {
        if (ctrl.signal.aborted) {
          setIsGenerating(false);
          return;
        }
        try {
          finish(await postChat(content, serverId, ctxWithMap));
        } catch (e2) {
          patch(t("assistant.offlineBackend"));
          setIsGenerating(false);
          abortRef.current = null;
        }
      }
    },
    [activeConversation, applyUiActions]
  );

  useEffect(() => {
    sendRef.current = handleSend;
  }, [handleSend]);

  // Leaving the page must not leave a dangling SSE request behind.
  useEffect(() => () => abortRef.current?.(), []);

  const handleSelectConversation = useCallback(
    (id: string) => {
      setMessages(threadsRef.current[id] ?? [welcome]);
      setActiveConversation(id);
      setMobileSidebarOpen(false);
    },
    []
  );

  const handleDeleteConversation = useCallback((id: string) => {
    delete threadsRef.current[id];
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (id === activeConversation) {
      threadsRef.current["conv-default"] = threadsRef.current["conv-default"] ?? [welcome];
      setMessages(threadsRef.current["conv-default"]);
      setActiveConversation("conv-default");
    }
  }, [activeConversation, welcome]);

  const handlePromptSelect = useCallback(
    (prompt: string) => {
      handleSend(prompt);
    },
    [handleSend]
  );

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-4rem)] -m-4 lg:-m-6">
        <div className="hidden lg:flex">
          <ConversationSidebar
            conversations={conversations}
            activeId={activeConversation}
            onSelect={handleSelectConversation}
            onNew={createNewConversation}
            onDelete={handleDeleteConversation}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>

        <AnimatePresence>
          {mobileSidebarOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setMobileSidebarOpen(false)}
                className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
              />
              <motion.div
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
                className="fixed inset-y-0 left-0 z-50 w-72 lg:hidden"
              >
                <ConversationSidebar
                  conversations={conversations}
                  activeId={activeConversation}
                  onSelect={handleSelectConversation}
                  onNew={createNewConversation}
                  onDelete={handleDeleteConversation}
                  isCollapsed={false}
                  onToggleCollapse={() => setMobileSidebarOpen(false)}
                />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <div className="flex flex-1 flex-col min-w-0 bg-background">
          <div className="flex items-center justify-between border-b border-border px-4 py-2 lg:hidden">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="flex items-center gap-2 text-sm font-medium text-foreground"
            >
              <MessageSquare className="h-4 w-4" />
              Conversations
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={createNewConversation}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground"
              >
                <Sparkles className="h-3.5 w-3.5" />
                New Chat
              </button>
            </div>
          </div>

          {messages.length === 1 && messages[0].id === "welcome" && !isGenerating ? (
            <div className="flex-1 flex flex-col items-center justify-center overflow-y-auto px-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="mb-8 text-center"
              >
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <h1 className="text-2xl font-bold text-foreground">
                  CropPilot AI Assistant
                </h1>
                <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
                  Your intelligent farming companion — ask anything about agriculture
                </p>
              </motion.div>
              <SuggestedPrompts onSelect={handlePromptSelect} />
            </div>
          ) : (
            <ChatMessages messages={messages} isGenerating={isGenerating} />
          )}

          <ChatInput
            onSend={handleSend}
            disabled={isGenerating}
            voiceStartSignal={voiceSignal}
            placeholder={t("assistant.placeholder")}
            suggestedPrompts={
              messages.length <= 1
                ? [
                    t("assistant.promptPaddy"),
                    t("assistant.promptDisease"),
                    t("assistant.promptMarket"),
                    t("assistant.promptSchemes"),
                  ]
                : undefined
            }
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
