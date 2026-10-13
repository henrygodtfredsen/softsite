"use client";

import { Layers, Moon, Sun } from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";

import Legend from "@/components/legend";
import type { FlyTarget, HoverInfo } from "@/components/map-view";
import ParcelPanel from "@/components/parcel-panel";
import SearchBox from "@/components/search-box";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { type DetailIndex, loadDetails, loadParcels, loadPlanAreas, loadPlanLabels } from "@/lib/data";
import { formatApn } from "@/lib/format";
import type { ColorMode, FamilyCode, Meta, ParcelCollection, Theme } from "@/lib/types";

// MapLibre needs the browser, so the map is never rendered on the server.
const MapView = dynamic(() => import("@/components/map-view"), { ssr: false });

const THEME_KEY = "softsite-theme";

function bboxOf(geom: GeoJSON.Polygon | GeoJSON.MultiPolygon): [number, number, number, number] {
  let w = Infinity, s = Infinity, e = -Infinity, n = -Infinity;
  const rings = geom.type === "Polygon" ? geom.coordinates : geom.coordinates.flat();
  for (const ring of rings) {
    for (const [x, y] of ring) {
      if (x < w) w = x;
      if (x > e) e = x;
      if (y < s) s = y;
      if (y > n) n = y;
    }
  }
  return [w, s, e, n];
}

// The theme lives on <html class="dark">, set before first paint by the inline
// script in layout.tsx. Components read it from there instead of copying it
// into React state, so the two can never disagree.
function subscribeTheme(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}
const themeSnapshot = (): Theme => (document.documentElement.classList.contains("dark") ? "dark" : "light");
const serverThemeSnapshot = (): Theme => "light";

export default function AppShell({ meta }: { meta: Meta }) {
  const theme = useSyncExternalStore(subscribeTheme, themeSnapshot, serverThemeSnapshot);
  const [parcels, setParcels] = useState<ParcelCollection | null>(null);
  const [planAreas, setPlanAreas] = useState<GeoJSON.FeatureCollection | null>(null);
  const [planLabels, setPlanLabels] = useState<GeoJSON.FeatureCollection | null>(null);
  const [details, setDetails] = useState<DetailIndex | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<ColorMode>("zoning");
  const [isolated, setIsolated] = useState<FamilyCode | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [pickedAddress, setPickedAddress] = useState<string | null>(null); // title the panel with what was searched
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const [flyTo, setFlyTo] = useState<FlyTarget | null>(null);

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.classList.toggle("dark", next === "dark");
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* private browsing: the choice just won't persist */
    }
  };

  useEffect(() => {
    loadParcels()
      .then((p) => {
        setParcels(p);
        // Panel details and plan outlines load right after the map has its parcels.
        loadDetails().then(setDetails).catch((e: Error) => setLoadError(e.message));
      })
      .catch((e: Error) => setLoadError(e.message));
    loadPlanAreas().then(setPlanAreas).catch(() => {});
    loadPlanLabels().then(setPlanLabels).catch(() => {});
  }, []);

  const featureByKey = useMemo(() => new Map(parcels?.features.map((f) => [f.properties.k, f]) ?? []), [parcels]);
  const parcelKeys = useMemo(() => [...featureByKey.keys()], [featureByKey]);

  const select = useCallback((key: string | null) => {
    setSelectedKey(key);
    setPickedAddress(null);
  }, []);

  const pickFromSearch = useCallback(
    (key: string, address: string | null) => {
      const f = featureByKey.get(key);
      setSelectedKey(key);
      setPickedAddress(address);
      if (f) setFlyTo((prev) => ({ bbox: bboxOf(f.geometry), seq: (prev?.seq ?? 0) + 1 }));
    },
    [featureByKey],
  );

  const detail = selectedKey ? (details ? (details.get(selectedKey) ?? null) : undefined) : undefined;
  const hoverDetail = hover && details ? details.get(hover.key) : undefined;

  return (
    <div className="flex h-dvh flex-col">
      <header className="z-30 flex h-14 shrink-0 items-center gap-3 border-b bg-background px-3 md:gap-6 md:px-4">
        <div className="flex shrink-0 items-baseline gap-2">
          <span className="text-[17px] font-semibold tracking-tight">SoftSite</span>
          <span className="hidden text-xs text-muted-foreground lg:inline">Santa Clara redevelopment screener</span>
        </div>
        <div className="flex min-w-0 flex-1 justify-center">
          <SearchBox parcelKeys={parcelKeys} onPick={pickFromSearch} />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={colorMode}
            onValueChange={(v) => v && setColorMode(v as ColorMode)}
            aria-label="Color parcels by"
            className="hidden sm:flex"
          >
            <ToggleGroupItem value="zoning" className="px-3 text-xs">
              Zoning
            </ToggleGroupItem>
            <ToggleGroupItem value="plans" className="px-3 text-xs">
              Plan areas
            </ToggleGroupItem>
          </ToggleGroup>
          <Button
            variant="outline"
            size="icon"
            className="sm:hidden"
            aria-label={colorMode === "zoning" ? "Color by plan area" : "Color by zoning"}
            onClick={() => setColorMode(colorMode === "zoning" ? "plans" : "zoning")}
          >
            <Layers />
          </Button>
          <Button
            variant="outline"
            size="icon"
            aria-label={theme === "dark" ? "Switch to light map" : "Switch to dark map"}
            onClick={toggleTheme}
          >
            {theme === "dark" ? <Sun /> : <Moon />}
          </Button>
        </div>
      </header>

      <main className="relative min-h-0 flex-1">
        {parcels && (
          <MapView
            parcels={parcels}
            planAreas={planAreas}
            planLabels={planLabels}
            bounds={meta.bounds}
            theme={theme}
            colorMode={colorMode}
            isolated={colorMode === "zoning" ? isolated : null}
            selectedKey={selectedKey}
            flyTo={flyTo}
            panelOpen={selectedKey !== null}
            hovering={hover !== null}
            onSelect={select}
            onHover={setHover}
          />
        )}

        {!parcels && !loadError && (
          <div className="absolute inset-0 grid place-items-center bg-muted/40">
            <p className="text-sm text-muted-foreground">
              Loading {meta.counts.parcels_mapped.toLocaleString("en-US")} parcels…
            </p>
          </div>
        )}

        {loadError && (
          <div className="absolute inset-0 z-40 grid place-items-center bg-background/80 p-6">
            <div className="max-w-sm rounded-xl border bg-background p-5 text-sm shadow-lg">
              <p className="font-medium">The parcel data didn&apos;t load.</p>
              <p className="mt-1 text-muted-foreground">{loadError}. Check your connection and reload the page.</p>
            </div>
          </div>
        )}

        {parcels && (
          <div className="pointer-events-none absolute top-3 left-3 z-10 hidden md:block">
            <Legend meta={meta} theme={theme} colorMode={colorMode} isolated={isolated} onIsolate={setIsolated} />
          </div>
        )}

        {hover && hover.key !== selectedKey && (
          <div
            className="pointer-events-none absolute z-20 hidden max-w-64 rounded-md border bg-background/95 px-2.5 py-1.5 text-xs shadow-md md:block"
            style={{ left: hover.x + 14, top: hover.y + 14 }}
          >
            <div className="font-medium">
              {hoverDetail?.addresses[0] ??
                (hover.key.startsWith("CITY-") ? "Condo common area" : `APN ${formatApn(hover.key)}`)}
            </div>
            <div className="text-muted-foreground">
              {hover.props.z
                ? `${hover.props.z} · ${meta.families.find((f) => f.code === hover.props.f)?.label}`
                : "No zoning in City GIS"}
              {hover.props.sp && ` · ${meta.lookups.specific_plan[hover.props.sp] ?? hover.props.sp}`}
            </div>
          </div>
        )}

        {selectedKey && (
          <ParcelPanel
            meta={meta}
            theme={theme}
            detail={detail}
            preferredAddress={pickedAddress}
            onClose={() => select(null)}
          />
        )}
      </main>
    </div>
  );
}
