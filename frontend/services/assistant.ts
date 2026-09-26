import { apiFetch } from "./api";

export interface AssistantCitation {
  source: string;
  title: string;
  snippet: string;
  score?: number | null;
}

export interface AssistantUIAction {
  action: string;
  payload: Record<string, unknown>;
}

export interface AssistantReply {
  text: string;
  conversation_id?: string | null;
  provider?: string | null;
  citations: AssistantCitation[];
  ui_actions: AssistantUIAction[];
}

export interface StreamCallbacks {
  onDelta?: (delta: string) => void;
  onTool?: (tool: string, status: string) => void;
  onFinal?: (reply: AssistantReply) => void;
  onError?: (message: string) => void;
  signal?: AbortSignal;
}

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Safe page-aware context (V1.3 §32): route + visible filters + UI
 *  language. Never secrets, tokens, or DOM dumps. */
export interface PageContext {
  route?: string;
  page?: string;
  language?: string;
  page_filters?: Record<string, unknown>;
}

/** Build page context from the current location. Callers add their own
 *  page_filters (e.g. market filter state); route/page/language are automatic. */
export function pageContext(
  filters?: Record<string, string | number | boolean>
): PageContext {
  const route =
    typeof window !== "undefined" ? window.location.pathname.slice(0, 64) : undefined;
  let language: string | undefined;
  try {
    const raw = localStorage.getItem("croppilot-locale");
    if (raw) language = (JSON.parse(raw)?.state?.locale as string) ?? undefined;
  } catch {
    // ignore: language simply omitted
  }
  return { route, language, ...(filters ? { page_filters: filters } : {}) };
}

function authHeaders(): Record<string, string> {
  // Token lives in the zustand auth store (persisted to localStorage).
  try {
    const raw = localStorage.getItem("croppilot-auth");
    if (raw) {
      const parsed = JSON.parse(raw);
      const token = parsed?.state?.token ?? parsed?.token;
      if (token) return { Authorization: `Bearer ${token}` };
    }
  } catch {
    // fall through without auth; backend dev bypass still answers
  }
  return {};
}

/** Non-streaming turn. Auth via apiFetch (zustand token). */
export function postChat(
  message: string,
  conversationId?: string,
  pageContext?: PageContext
): Promise<AssistantReply> {
  return apiFetch<AssistantReply>("/api/v1/assistant/chat", {
    method: "POST",
    body: { message, conversation_id: conversationId ?? null, ...(pageContext ?? {}) },
  });
}

/**
 * SSE turn. Resolves true when the stream completes; false when the
 * caller should fall back to postChat (network/SSE failure).
 */
export async function streamChat(
  message: string,
  conversationId: string | undefined,
  cb: StreamCallbacks,
  pageContext?: PageContext
): Promise<boolean> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/assistant/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        message,
        conversation_id: conversationId ?? null,
        ...(pageContext ?? {}),
      }),
      signal: cb.signal,
    });
  } catch {
    return false;
  }
  if (!res.ok || !res.body) return false;

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event = "";
  let done = false;

  const dispatch = (ev: string, raw: string) => {
    let data: unknown = raw;
    try {
      data = JSON.parse(raw);
    } catch {
      // keep raw string
    }
    if (ev === "delta" && typeof data === "string") cb.onDelta?.(data);
    else if (ev === "tool" && data && typeof data === "object") {
      const t = data as { tool?: string; status?: string };
      cb.onTool?.(t.tool ?? "tool", t.status ?? "");
    } else if (ev === "final" && data && typeof data === "object") {
      done = true;
      const f = data as Record<string, unknown>;
      cb.onFinal?.({
        text: String(f.text ?? ""),
        conversation_id:
          (f.conversation_id as string) ?? (f.message_id as string) ?? undefined,
        provider: (f.provider as { name?: string } | undefined)?.name ?? null,
        citations: (f.citations as AssistantCitation[]) ?? [],
        ui_actions: (f.ui_actions as AssistantUIAction[]) ?? [],
      });
    } else if (ev === "error") {
      cb.onError?.(typeof data === "string" ? data : "Assistant unavailable");
    }
  };

  for (;;) {
    const { value, done: readerDone } = await reader.read();
    if (readerDone) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      let dataRaw = "";
      for (const line of part.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataRaw += line.slice(5).trim();
      }
      if (event) dispatch(event, dataRaw);
      event = "";
    }
  }
  return done;
}

/** Cross-page bridge (§23): any page can push a user message into the assistant. */
export function sendToChat(text: string): void {
  window.dispatchEvent(new CustomEvent<string>("croppilot:send-chat", { detail: text }));
}

export type { MapAssistantContext } from "./map";
export { takeMapAssistantContext } from "./map";
