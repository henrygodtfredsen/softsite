// Loads the static data files once and caches the promise, so every component
// that asks gets the same in-flight request.

import type { ParcelCollection, ParcelDetail } from "./types";

const cache = new Map<string, Promise<unknown>>();

function loadJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    const p = fetch(path).then((res) => {
      if (!res.ok) throw new Error(`Could not load ${path} (HTTP ${res.status})`);
      return res.json();
    });
    p.catch(() => cache.delete(path)); // allow a retry after a failure
    cache.set(path, p);
  }
  return cache.get(path) as Promise<T>;
}

export const loadParcels = () => loadJson<ParcelCollection>("/data/parcels.geojson");
export const loadPlanAreas = () => loadJson<GeoJSON.FeatureCollection>("/data/plan_areas.geojson");
export const loadPlanLabels = () => loadJson<GeoJSON.FeatureCollection>("/data/plan_labels.geojson");
export const loadSearchIndex = () => loadJson<[string, string][]>("/data/search_index.json");

/** parcel_details.json is column-oriented ({fields, rows}); expand rows on demand. */
export type DetailIndex = { get(key: string): ParcelDetail | undefined };

export async function loadDetails(): Promise<DetailIndex> {
  const raw = await loadJson<{ fields: string[]; rows: Record<string, unknown[]> }>("/data/parcel_details.json");
  return {
    get(key) {
      const row = raw.rows[key];
      if (!row) return undefined;
      return Object.fromEntries(raw.fields.map((f, i) => [f, row[i]])) as unknown as ParcelDetail;
    },
  };
}
