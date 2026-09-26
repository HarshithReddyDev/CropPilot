"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";

/**
 * True once the persisted auth state has been rehydrated.
 *
 * With synchronous storage this is already true on first render, but
 * protected queries must still wait for it explicitly: firing them
 * beforehand sends unauthenticated requests that fail and, once retries
 * are exhausted, leave the page stuck in an outage state that only a
 * filter change (new query keys) would clear.
 */
export function useAuthReady(): boolean {
  // Start false on both server and client so the first render matches,
  // then resolve on mount. This keeps the initial paint a skeleton
  // instead of risking a hydration mismatch or a premature error panel.
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setReady(true);
      return;
    }
    const unsub = useAuthStore.persist.onFinishHydration(() => setReady(true));
    return unsub;
  }, []);

  return ready;
}
