"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { getVersion, setWorkerUrl } from "maplibre-gl";
import { useCallback, useEffect, useRef } from "react";
import Map, {
  AttributionControl,
  Layer,
  NavigationControl,
  ScaleControl,
  Source,
  type MapLayerMouseEvent,
  type MapRef,
} from "react-map-gl/maplibre";

import { BASEMAP, fillColor, fillOpacity, INK } from "@/lib/map-style";
import type { ColorMode, FamilyCode, ParcelCollection, ParcelFeatureProps, Theme } from "@/lib/types";

export interface HoverInfo {
  key: string;
  props: ParcelFeatureProps;
  x: number;
  y: number;
}

export interface FlyTarget {
  bbox: [number, number, number, number];
  seq: number; // bump to re-trigger for the same parcel
}

interface Props {
  parcels: ParcelCollection;
  planAreas: GeoJSON.FeatureCollection | null;
  planLabels: GeoJSON.FeatureCollection | null;
  bounds: [number, number, number, number];
  theme: Theme;
  colorMode: ColorMode;
  isolated: FamilyCode | null;
  selectedKey: string | null;
  flyTo: FlyTarget | null;
  panelOpen: boolean;
  hovering: boolean;
  onSelect: (key: string | null) => void;
  onHover: (info: HoverInfo | null) => void;
}

// Served from public/vendor/ (copied there on npm install by
// scripts/copy-maplibre-worker.mjs); the version query busts browser caches.
setWorkerUrl(`/vendor/maplibre-gl-worker.mjs?v=${getVersion()}`);

const PARCEL_SOURCE = "parcels";
const FILL_LAYER = "parcel-fill";

export default function MapView({
  parcels,
  planAreas,
  planLabels,
  bounds,
  theme,
  colorMode,
  isolated,
  selectedKey,
  flyTo,
  panelOpen,
  hovering,
  onSelect,
  onHover,
}: Props) {
  const mapRef = useRef<MapRef>(null);
  const hoveredRef = useRef<string | null>(null);
  const ink = INK[theme];

  const setHoverState = useCallback((key: string | null) => {
    const map = mapRef.current;
    if (!map || hoveredRef.current === key) return;
    if (hoveredRef.current) map.setFeatureState({ source: PARCEL_SOURCE, id: hoveredRef.current }, { hover: false });
    if (key) map.setFeatureState({ source: PARCEL_SOURCE, id: key }, { hover: true });
    hoveredRef.current = key;
  }, []);

  const handleMove = useCallback(
    (e: MapLayerMouseEvent) => {
      const f = e.features?.[0];
      if (!f) {
        setHoverState(null);
        onHover(null);
        return;
      }
      const props = f.properties as ParcelFeatureProps;
      setHoverState(props.k);
      onHover({ key: props.k, props, x: e.point.x, y: e.point.y });
    },
    [onHover, setHoverState],
  );

  const handleLeave = useCallback(() => {
    setHoverState(null);
    onHover(null);
  }, [onHover, setHoverState]);

  const handleClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const f = e.features?.[0];
      onSelect(f ? (f.properties as ParcelFeatureProps).k : null);
      // On phones the detail sheet covers the lower half; slide a tapped
      // parcel up so it stays visible above the sheet.
      const map = mapRef.current;
      if (f && map && window.innerWidth < 768) {
        const h = map.getContainer().clientHeight;
        if (e.point.y > h * 0.4) map.panBy([0, e.point.y - h * 0.25], { duration: 400 });
      }
    },
    [onSelect],
  );

  // Fly to a parcel chosen from search, leaving room for the detail panel.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !flyTo) return;
    const [w, s, e, n] = flyTo.bbox;
    const wide = window.innerWidth >= 768;
    map.fitBounds(
      [
        [w, s],
        [e, n],
      ],
      {
        padding: wide
          ? { top: 80, bottom: 80, left: 80, right: panelOpen ? 440 : 80 }
          : { top: 60, bottom: Math.round(window.innerHeight * 0.5), left: 30, right: 30 },
        maxZoom: 18,
        duration: 900,
      },
    );
    // Only re-run when a new fly target arrives.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flyTo]);

  const selectedFilter = ["==", ["get", "k"], selectedKey ?? "__none__"] as const;

  return (
    <Map
      ref={mapRef}
      mapStyle={BASEMAP[theme]}
      initialViewState={{
        bounds: [
          [bounds[0], bounds[1]],
          [bounds[2], bounds[3]],
        ],
        // Leave room for the legend card on wider screens.
        fitBoundsOptions: {
          padding:
            typeof window !== "undefined" && window.innerWidth >= 768
              ? { top: 30, bottom: 30, left: 310, right: 30 }
              : 20,
        },
      }}
      minZoom={10}
      maxZoom={19}
      interactiveLayerIds={[FILL_LAYER]}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      onClick={handleClick}
      cursor={hovering ? "pointer" : "grab"}
      attributionControl={false}
      style={{ position: "absolute", inset: 0 }}
    >
      <Source id={PARCEL_SOURCE} type="geojson" data={parcels} promoteId="k">
        <Layer
          id={FILL_LAYER}
          type="fill"
          paint={{
            "fill-color": fillColor(theme, colorMode, isolated),
            "fill-opacity": fillOpacity(colorMode, isolated),
          }}
        />
        <Layer
          id="parcel-outline"
          type="line"
          minzoom={13.5}
          paint={{
            "line-color": ink.outline,
            "line-width": ["interpolate", ["linear"], ["zoom"], 13.5, 0.2, 16, 0.6, 18, 1],
          }}
        />
        <Layer
          id="parcel-hover"
          type="line"
          paint={{
            "line-color": ink.selected,
            "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 1.6, 0],
          }}
        />
        <Layer
          id="parcel-selected-halo"
          type="line"
          filter={selectedFilter as never}
          paint={{ "line-color": ink.halo, "line-width": 6, "line-opacity": 0.9 }}
        />
        <Layer
          id="parcel-selected"
          type="line"
          filter={selectedFilter as never}
          paint={{ "line-color": ink.selected, "line-width": 2.5 }}
        />
      </Source>

      {planAreas && (
        <Source id="plan-areas" type="geojson" data={planAreas}>
          <Layer
            id="plan-outline"
            type="line"
            paint={{
              "line-color": ink.plan,
              "line-width": colorMode === "plans" ? 2.2 : 1.4,
              "line-dasharray": [3, 2],
              "line-opacity": 0.85,
            }}
          />
        </Source>
      )}
      {planLabels && (
        <Source id="plan-labels" type="geojson" data={planLabels}>
          <Layer
            id="plan-label"
            type="symbol"
            layout={{
              "text-field": ["get", "label"],
              "text-font": ["Noto Sans Bold"],
              "text-size": ["interpolate", ["linear"], ["zoom"], 11, 11, 15, 14],
              "text-max-width": 9,
              "text-allow-overlap": false,
            }}
            paint={{
              "text-color": ink.plan,
              "text-halo-color": ink.halo,
              "text-halo-width": 1.6,
            }}
          />
        </Source>
      )}

      <NavigationControl position="bottom-right" showCompass={false} />
      <ScaleControl position="bottom-right" unit="imperial" />
      <AttributionControl position="bottom-right" compact />
    </Map>
  );
}
