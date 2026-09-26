"use client";

import { useState, useRef, useEffect, useId } from "react";
import { useTranslation } from "@/lib/i18n";
import { useMapSearch } from "@/hooks/use-map";
import type { MapSearchResult } from "@/services/map";

interface MapSearchProps {
  onPick: (r: MapSearchResult) => void;
}

function useDebounced(value: string, ms: number): string {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}

/** Location search: village/town/city/district/state/PIN plus known
 *  CropPilot market names. Debounced, keyboard-navigable, screen-reader
 *  labeled. Queries the backend only (never third parties from the browser). */
export function MapSearch({ onPick }: MapSearchProps) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const boxRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const debounced = useDebounced(q, 300);
  const query = useMapSearch(open ? debounced : "");
  const results = query.data ?? [];

  useEffect(() => {
    setActive(-1);
  }, [debounced]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const pick = (r: MapSearchResult) => {
    setOpen(false);
    setQ(r.name);
    onPick(r);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!open || results.length === 0) {
      if (e.key === "Enter") setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(results[active >= 0 ? active : 0]);
    }
  };

  const sub = (r: MapSearchResult) =>
    [r.district, r.state].filter(Boolean).join(", ") || null;

  return (
    <div ref={boxRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-background/95 py-2 pe-2 ps-3 shadow-sm backdrop-blur">
        <svg className="h-4 w-4 shrink-0 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" strokeLinecap="round" />
        </svg>
        <input
          value={q}
          role="combobox"
          aria-expanded={open && results.length > 0}
          aria-controls={listId}
          aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
          aria-label={t("maps.searchLocation")}
          placeholder={t("maps.searchLocation")}
          autoComplete="off"
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        {query.isFetching && (
          <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" aria-hidden="true" />
        )}
        {q && (
          <button
            type="button"
            onClick={() => {
              setQ("");
              setOpen(false);
            }}
            aria-label={t("maps.clearSearch")}
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-muted"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path d="M6 18 18 6M6 6l12 12" strokeLinecap="round" />
            </svg>
          </button>
        )}
      </div>
      {open && q.trim().length >= 2 && (
        <div className="absolute inset-x-0 top-full z-30 mt-1 overflow-hidden rounded-xl border border-border bg-background shadow-xl">
          {query.isError ? (
            <p className="px-4 py-3 text-sm text-muted-foreground" role="alert">
              {t("maps.searchFailed")}
            </p>
          ) : !query.isFetching && results.length === 0 ? (
            <p className="px-4 py-3 text-sm text-muted-foreground">{t("maps.noResults")}</p>
          ) : (
            <ul id={listId} role="listbox" aria-label={t("maps.searchLocation")} className="max-h-64 overflow-y-auto py-1">
              {results.map((r, i) => (
                <li key={`${r.source}-${r.type}-${r.name}-${i}`}>
                  <button
                    type="button"
                    role="option"
                    id={`${listId}-${i}`}
                    aria-selected={i === active}
                    onClick={() => pick(r)}
                    onMouseEnter={() => setActive(i)}
                    className={`flex w-full flex-col gap-0.5 px-4 py-2 text-left text-sm transition-colors ${
                      i === active ? "bg-muted" : ""
                    }`}
                  >
                    <span className="font-medium text-foreground">
                      {r.name}
                      {r.latitude == null && (
                        <span className="ms-2 text-[10px] font-normal text-muted-foreground">
                          {r.type}
                        </span>
                      )}
                    </span>
                    {sub(r) && <span className="text-xs text-muted-foreground">{sub(r)}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
