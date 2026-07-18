import { create } from "zustand";
import type { H3HexFeature } from "@/types";

interface TelemetryState {
  hexFeatures: H3HexFeature[];
  isConnected: boolean;
  lastUpdate: number | null;
  updateRate: number;
  setHexFeatures: (features: H3HexFeature[]) => void;
  batchUpdateHexFeatures: (features: H3HexFeature[]) => void;
  upsertHexFeatures: (features: H3HexFeature[]) => void;
  setConnected: (connected: boolean) => void;
  clearHexFeatures: () => void;
}

export const useTelemetryStore = create<TelemetryState>()((set, get) => ({
  hexFeatures: [],
  isConnected: false,
  lastUpdate: null,
  updateRate: 0,

  setHexFeatures: (features) =>
    set({
      hexFeatures: features,
      lastUpdate: Date.now(),
    }),

  batchUpdateHexFeatures: (features) =>
    set({
      hexFeatures: features,
      lastUpdate: Date.now(),
    }),

  upsertHexFeatures: (features) => {
    const existing = get().hexFeatures;
    const existingMap = new Map(existing.map((f) => [f.h3_index, f]));

    for (const feature of features) {
      existingMap.set(feature.h3_index, {
        ...existingMap.get(feature.h3_index),
        ...feature,
      });
    }

    set({
      hexFeatures: Array.from(existingMap.values()),
      lastUpdate: Date.now(),
    });
  },

  setConnected: (connected) =>
    set({
      isConnected: connected,
      ...(connected ? {} : { updateRate: 0 }),
    }),

  clearHexFeatures: () =>
    set({
      hexFeatures: [],
      lastUpdate: null,
      updateRate: 0,
    }),
}));
