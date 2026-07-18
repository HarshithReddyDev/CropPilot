import { apiPost } from "./api";
import type { ChatMessage } from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatRequest {
  message: string;
  conversation_id?: string;
  plot_id?: string;
}

interface ChatResponse {
  message: ChatMessage;
  conversation_id: string;
}

interface RAGRequest {
  query: string;
  h3_index?: string;
  top_k?: number;
}

interface RAGResponse {
  answer: string;
  sources: { title: string; content: string; score: number }[];
}

export async function sendChatMessage(
  data: ChatRequest
): Promise<ChatResponse> {
  return apiPost<ChatResponse>("/api/v1/chat/message", data);
}

export function streamChatMessage(
  data: ChatRequest
): { stream: ReadableStream<Uint8Array>; abort: () => void } {
  const token = localStorage.getItem("croppilot-auth")
    ? (JSON.parse(localStorage.getItem("croppilot-auth")!) as { state: { token: string } })
        ?.state?.token
    : null;

  const abortController = new AbortController();

  const url = `${BASE_URL}/api/v1/chat/message/stream`;

  const body = JSON.stringify(data);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const responsePromise = fetch(url, {
    method: "POST",
    headers,
    body,
    signal: abortController.signal,
  });

  let streamResolver: (stream: ReadableStream<Uint8Array>) => void;
  let streamRejecter: (err: unknown) => void;
  const streamPromise = new Promise<ReadableStream<Uint8Array>>(
    (resolve, reject) => {
      streamResolver = resolve;
      streamRejecter = reject;
    }
  );

  responsePromise
    .then((response) => {
      if (!response.ok) {
        streamRejecter(
          new Error(`Stream request failed with status ${response.status}`)
        );
        return;
      }
      streamResolver(response.body!);
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        streamRejecter(err);
      }
    });

  return {
    get stream() {
      return streamPromise;
    },
    abort: () => abortController.abort(),
  } as unknown as { stream: ReadableStream<Uint8Array>; abort: () => void };
}

export function streamRAG(
  data: RAGRequest
): { stream: Promise<ReadableStream<Uint8Array>>; abort: () => void } {
  const token = localStorage.getItem("croppilot-auth")
    ? (JSON.parse(localStorage.getItem("croppilot-auth")!) as { state: { token: string } })
        ?.state?.token
    : null;

  const abortController = new AbortController();

  const url = `${BASE_URL}/api/v1/rag/stream`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const responsePromise = fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
    signal: abortController.signal,
  });

  let streamResolver: (stream: ReadableStream<Uint8Array>) => void;
  let streamRejecter: (err: unknown) => void;
  const streamPromise = new Promise<ReadableStream<Uint8Array>>(
    (resolve, reject) => {
      streamResolver = resolve;
      streamRejecter = reject;
    }
  );

  responsePromise
    .then((response) => {
      if (!response.ok) {
        streamRejecter(
          new Error(`RAG stream failed with status ${response.status}`)
        );
        return;
      }
      streamResolver(response.body!);
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        streamRejecter(err);
      }
    });

  return { stream: streamPromise, abort: () => abortController.abort() };
}

export function streamIntel(
  data: RAGRequest
): { stream: Promise<ReadableStream<Uint8Array>>; abort: () => void } {
  const token = localStorage.getItem("croppilot-auth")
    ? (JSON.parse(localStorage.getItem("croppilot-auth")!) as { state: { token: string } })
        ?.state?.token
    : null;

  const abortController = new AbortController();

  const url = `${BASE_URL}/api/v1/intel/stream`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const responsePromise = fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
    signal: abortController.signal,
  });

  let streamResolver: (stream: ReadableStream<Uint8Array>) => void;
  let streamRejecter: (err: unknown) => void;
  const streamPromise = new Promise<ReadableStream<Uint8Array>>(
    (resolve, reject) => {
      streamResolver = resolve;
      streamRejecter = reject;
    }
  );

  responsePromise
    .then((response) => {
      if (!response.ok) {
        streamRejecter(
          new Error(`Intel stream failed with status ${response.status}`)
        );
        return;
      }
      streamResolver(response.body!);
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        streamRejecter(err);
      }
    });

  return { stream: streamPromise, abort: () => abortController.abort() };
}
