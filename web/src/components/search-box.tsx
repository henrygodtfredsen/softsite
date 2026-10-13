"use client";

import { Search } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { loadSearchIndex } from "@/lib/data";
import { formatApn } from "@/lib/format";

interface Result {
  key: string;
  primary: string;
  secondary: string;
  isAddress: boolean;
}

interface Props {
  parcelKeys: string[]; // every parcel key on the map, for APN search
  onPick: (key: string, address: string | null) => void;
}

const MAX_RESULTS = 8;

function searchAddresses(index: [string, string][], q: string): Result[] {
  const needle = q.toLowerCase();
  const starts: Result[] = [];
  const contains: Result[] = [];
  for (const [address, key] of index) {
    const hay = address.toLowerCase();
    const pos = hay.indexOf(needle);
    if (pos < 0) continue;
    const r = {
      key,
      primary: address,
      secondary: key.startsWith("CITY-") ? key.slice(5) : `APN ${formatApn(key)}`,
      isAddress: true,
    };
    (pos === 0 ? starts : contains).push(r);
    if (starts.length >= MAX_RESULTS) break;
  }
  return [...starts, ...contains].slice(0, MAX_RESULTS);
}

function searchApns(keys: string[], digits: string): Result[] {
  const out: Result[] = [];
  for (const key of keys) {
    if (key.startsWith(digits)) {
      out.push({ key, primary: `APN ${formatApn(key)}`, secondary: "Parcel", isAddress: false });
      if (out.length >= MAX_RESULTS) break;
    }
  }
  return out;
}

export default function SearchBox({ parcelKeys, onPick }: Props) {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState<[string, string][] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const listId = useId();
  const wrapRef = useRef<HTMLDivElement>(null);

  const ensureIndex = () => {
    if (index || error) return;
    loadSearchIndex()
      .then(setIndex)
      .catch((e: Error) => setError(e.message));
  };

  const results = useMemo<Result[]>(() => {
    const q = query.trim();
    if (q.length < 2) return [];
    // Mostly digits and dashes -> treat as an APN.
    if (/^[\d\s-]+$/.test(q)) {
      const digits = q.replace(/\D/g, "");
      if (digits.length >= 3) return searchApns(parcelKeys, digits);
    }
    return index ? searchAddresses(index, q) : [];
  }, [query, index, parcelKeys]);

  const activeIdx = Math.min(active, Math.max(results.length - 1, 0));

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const pick = (r: Result) => {
    onPick(r.key, r.isAddress ? r.primary : null);
    setQuery(r.primary);
    setOpen(false);
  };

  const q = query.trim();
  const showPanel = open && q.length >= 2;

  return (
    <div ref={wrapRef} className="relative w-full max-w-md">
      <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="search"
        role="combobox"
        aria-expanded={showPanel}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-label="Search by address or APN"
        placeholder="Search an address or APN"
        className="h-9 pl-8"
        value={query}
        onFocus={() => {
          ensureIndex();
          setOpen(true);
        }}
        onChange={(e) => {
          setQuery(e.target.value);
          setActive(0);
          setOpen(true);
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((i) => Math.min(i + 1, results.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((i) => Math.max(i - 1, 0));
          } else if (e.key === "Enter" && results[activeIdx]) {
            e.preventDefault();
            pick(results[activeIdx]);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
      />
      {showPanel && (
        <ul
          id={listId}
          role="listbox"
          className="absolute top-full right-0 left-0 z-30 mt-1 overflow-hidden rounded-md border bg-popover py-1 text-sm shadow-lg"
        >
          {error && <li className="px-3 py-2 text-muted-foreground">Address search is unavailable: {error}</li>}
          {!error && !index && !/^[\d\s-]+$/.test(q) && (
            <li className="px-3 py-2 text-muted-foreground">Loading addresses…</li>
          )}
          {!error && results.length === 0 && (index || /^[\d\s-]+$/.test(q)) && (
            <li className="px-3 py-2 text-muted-foreground">No Santa Clara address or APN matches “{q}”.</li>
          )}
          {results.map((r, i) => (
            <li
              key={`${r.key}-${r.primary}`}
              role="option"
              aria-selected={i === activeIdx}
              className={`cursor-pointer px-3 py-1.5 ${i === activeIdx ? "bg-accent" : ""}`}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(r);
              }}
            >
              <div className="truncate">{r.primary}</div>
              <div className="font-mono text-xs text-muted-foreground">{r.secondary}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
