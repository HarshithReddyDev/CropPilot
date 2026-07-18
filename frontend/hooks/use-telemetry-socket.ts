"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTelemetryStore } from "@/stores/telemetry-store";
import type { H3HexFeature } from "@/types";

const WS_URL = "wss://api.agricommand.dev/ws/spatial";

const H3_INDEXES = [
  "8928308280fffff",
  "8928308281fffff",
  "8928308282fffff",
  "8928308283fffff",
  "8928308284fffff",
  "8928308285fffff",
  "8928308286fffff",
  "8928308287fffff",
  "8928308288fffff",
  "8928308289fffff",
  "892830828afffff",
  "892830828bfffff",
  "892830828cfffff",
  "892830828dfffff",
  "892830828efffff",
  "892830828ffffff",
];

interface MockPayload {
  type: "spatial_update";
  features: H3HexFeature[];
  timestamp: number;
}

function generateMockFeatures(): H3HexFeature[] {
  return H3_INDEXES.map((h3) => ({
    h3_index: h3,
    confidence: Math.random(),
    crop_type: ["Rice", "Wheat", "Cotton", "Sugarcane", "Maize"][
      Math.floor(Math.random() * 5)
    ],
    color: [
      255,
      Math.floor(Math.random() * 80) + 20,
      Math.floor(Math.random() * 60) + 40,
      180,
    ] as [number, number, number, number],
  }));
}

function createMockPayload(): MockPayload {
  return {
    type: "spatial_update",
    features: generateMockFeatures(),
    timestamp: Date.now(),
  };
}

interface TelemetrySocketOptions {
  useMockFallback?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onFeaturesUpdate?: (features: H3HexFeature[]) => void;
}

export function useTelemetrySocket(options: TelemetrySocketOptions = {}) {
  const {
    useMockFallback = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
    onFeaturesUpdate,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const mockTimerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const isMountedRef = useRef(true);

  const {
    setHexFeatures,
    upsertHexFeatures,
    setConnected,
    clearHexFeatures,
  } = useTelemetryStore();

  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = undefined;
    }
    if (mockTimerRef.current) {
      clearInterval(mockTimerRef.current);
      mockTimerRef.current = undefined;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const startMockData = useCallback(() => {
    setConnected(true);
    mockTimerRef.current = setInterval(() => {
      if (!isMountedRef.current) return;
      const payload = createMockPayload();
      if (onFeaturesUpdate) {
        onFeaturesUpdate(payload.features);
      } else {
        upsertHexFeatures(payload.features);
      }
    }, 50); // Increased frequency to simulate high-velocity stream (approx 20fps for testing)
  }, [setConnected, upsertHexFeatures, onFeaturesUpdate]);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    cleanup();

    if (useMockFallback) {
      startMockData();
      return;
    }

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as MockPayload;
          if (payload.type === "spatial_update" && payload.features) {
            if (onFeaturesUpdate) {
              onFeaturesUpdate(payload.features);
            } else {
              upsertHexFeatures(payload.features);
            }
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (isMountedRef.current) {
          reconnectAttemptsRef.current += 1;
          if (
            reconnectAttemptsRef.current < maxReconnectAttempts
          ) {
            reconnectTimerRef.current = setTimeout(() => {
              connect();
            }, reconnectInterval);
          }
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      if (useMockFallback) {
        startMockData();
      }
    }
  }, [
    cleanup,
    useMockFallback,
    startMockData,
    setConnected,
    upsertHexFeatures,
    onFeaturesUpdate,
    reconnectInterval,
    maxReconnectAttempts,
  ]);

  const disconnect = useCallback(() => {
    isMountedRef.current = false;
    cleanup();
    setConnected(false);
    clearHexFeatures();
  }, [cleanup, setConnected, clearHexFeatures]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
  };
}
