"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

interface UseIntersectionObserverOptions {
  threshold?: number | number[];
  root?: Element | Document | null;
  rootMargin?: string;
  triggerOnce?: boolean;
}

interface UseIntersectionObserverReturn {
  ref: RefObject<Element | null>;
  isIntersecting: boolean;
  intersectionRatio: number;
  entry: IntersectionObserverEntry | null;
}

export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {}
): UseIntersectionObserverReturn {
  const {
    threshold = 0,
    root = null,
    rootMargin = "0px",
    triggerOnce = false,
  } = options;

  const ref = useRef<Element | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [intersectionRatio, setIntersectionRatio] = useState(0);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(
    null
  );
  const hasTriggered = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    if (triggerOnce && hasTriggered.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        setIntersectionRatio(entry.intersectionRatio);
        setEntry(entry);

        if (entry.isIntersecting) {
          hasTriggered.current = true;
          if (triggerOnce) {
            observer.unobserve(element);
            observer.disconnect();
          }
        }
      },
      { threshold, root, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [threshold, root, rootMargin, triggerOnce]);

  return { ref, isIntersecting, intersectionRatio, entry };
}
