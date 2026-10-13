"use client";

import { fmtDate, fmtInt } from "@/lib/format";
import { COLOR_GROUPS } from "@/lib/map-style";
import type { ColorMode, FamilyCode, Meta, Theme } from "@/lib/types";

interface Props {
  meta: Meta;
  theme: Theme;
  colorMode: ColorMode;
  isolated: FamilyCode | null;
  onIsolate: (f: FamilyCode | null) => void;
}

function Swatch({ color, outlined }: { color: string; outlined?: boolean }) {
  return (
    <span
      aria-hidden
      className={`mt-0.5 size-3 shrink-0 rounded-[3px] ${outlined ? "border border-dashed border-foreground/40" : "border border-foreground/15"}`}
      style={{ background: color }}
    />
  );
}

export default function Legend({ meta, theme, colorMode, isolated, onIsolate }: Props) {
  const familyByCode = new Map(meta.families.map((f) => [f.code, f]));
  const parcelsSource = meta.sources.find((s) => s.id === "city_land_parcels")!;

  return (
    <div className="pointer-events-auto max-h-[calc(100vh-7rem)] w-[17rem] overflow-y-auto rounded-xl border bg-background/95 p-3.5 text-sm shadow-lg backdrop-blur">
      {colorMode === "zoning" ? (
        <>
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="font-medium">Zoning family</h2>
            {isolated && (
              <button className="text-xs text-link hover:underline" onClick={() => onIsolate(null)}>
                Show all
              </button>
            )}
          </div>
          <ul className="space-y-2.5">
            {COLOR_GROUPS.map((g) => (
              <li key={g.id}>
                <div className="flex items-start gap-2">
                  <Swatch color={g.color[theme]} outlined={g.id === "none"} />
                  <span className={g.neutral ? "text-muted-foreground" : "font-medium"}>{g.label}</span>
                </div>
                <ul className="mt-0.5 ml-5 space-y-0.5">
                  {g.families.map((code) => {
                    const fam = familyByCode.get(code);
                    if (!fam) return null;
                    const on = isolated === code;
                    return (
                      <li key={code}>
                        <button
                          className={`flex w-full items-baseline justify-between gap-2 rounded px-1.5 py-0.5 text-left text-xs hover:bg-accent ${on ? "bg-accent font-medium" : ""} ${isolated && !on ? "text-muted-foreground" : ""}`}
                          aria-pressed={on}
                          onClick={() => onIsolate(on ? null : code)}
                          title={on ? "Show all families" : `Show only ${fam.label}`}
                        >
                          <span>{fam.label}</span>
                          <span className="tabular-nums text-muted-foreground">{fmtInt(fam.count)}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ul>
          <p className="mt-2.5 text-xs text-muted-foreground">
            Click a family to show it alone. Colors group families so the map stays readable for colorblind
            viewers.
          </p>
        </>
      ) : (
        <>
          <h2 className="mb-2 font-medium">Specific plan &amp; focus areas</h2>
          <ul className="space-y-1">
            {meta.plans.map((p) => (
              <li key={p.code} className="flex items-baseline justify-between gap-2 text-xs">
                <span>{p.label}</span>
                <span className="tabular-nums text-muted-foreground">{fmtInt(p.parcel_count)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2.5 text-xs text-muted-foreground">
            Shaded parcels are inside a plan area; outlines are drawn around each plan&apos;s parcels.
          </p>
        </>
      )}
      <p className="mt-2.5 border-t pt-2 text-[11px] text-muted-foreground">
        {fmtInt(meta.counts.parcels_mapped)} parcels · {parcelsSource.attribution}, retrieved{" "}
        {fmtDate(parcelsSource.retrieved_at)}
      </p>
    </div>
  );
}
