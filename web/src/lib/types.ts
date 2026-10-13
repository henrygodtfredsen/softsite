// Shapes of the files the pipeline writes to web/public/data/ (see pipeline/steps/export.py).

export type FamilyCode =
  | "single_family"
  | "low_density_res"
  | "multifamily"
  | "mixed_use"
  | "commercial"
  | "office_rd"
  | "industrial"
  | "planned_dev"
  | "public_open"
  | "none";

export interface SourceInfo {
  id: string;
  name: string;
  url: string;
  attribution: string;
  retrieved_at: string;
  records: number;
}

export interface Meta {
  product: string;
  city: string;
  generated_at: string;
  bounds: [number, number, number, number];
  counts: { parcels_mapped: number; land_parcels: number; addresses_indexed: number };
  families: { code: FamilyCode; label: string; count: number }[];
  plans: { code: string; label: string; parcel_count: number; parcel_acres: number }[];
  lookups: {
    parcel_type: Record<string, string>;
    zoning: Record<string, { label: string; family: FamilyCode }>;
    general_plan: Record<string, string>;
    specific_plan: Record<string, string>;
    historic: Record<string, string>;
    flood: Record<string, string>;
  };
  sources: SourceInfo[];
  links: {
    zoning_code_home: string;
    zoning_code_label: string;
    general_plan_home: string;
    general_plan_label: string;
  };
}

/** Properties on each feature of parcels.geojson (kept short to keep the file small). */
export interface ParcelFeatureProps {
  k: string; // parcel key: 8-digit APN, or "CITY-<id>" for City-only common-area IDs
  f: FamilyCode;
  z: string; // zoning code
  sp: string; // specific plan code
  t: string; // parcel type code
}

export interface ParcelDetail {
  apn: string;
  is_assessor_apn: boolean;
  addresses: string[];
  address_count: number;
  parcel_type: string | null;
  zoning: string | null;
  general_plan: string | null;
  specific_plan: string | null;
  historic: string | null;
  flood: string | null;
  year_built: number | null;
  lot_area_sqft: number | null;
  lot_area_acres: number | null;
  acreage_published: number | null;
  zip: number | null;
  council_district: string | null;
  n_parts: number;
  object_ids: number[];
}

export type ParcelFeature = GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon, ParcelFeatureProps>;
export type ParcelCollection = GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon, ParcelFeatureProps>;

export type ColorMode = "zoning" | "plans";
export type Theme = "light" | "dark";
