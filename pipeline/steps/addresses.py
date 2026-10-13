"""Step `addresses`: pull the City's site-address points and attach each one
to the parcel it sits on, for address search. Writes data/processed/addresses.parquet."""

from __future__ import annotations

import json
import logging

import geopandas as gpd
import pandas as pd

from pipeline import arcgis
from pipeline.config import PROCESSED_DIR, Config
from pipeline.geo import features_to_gdf
from pipeline.http import PoliteClient
from pipeline.raw_store import RawStore
from pipeline.steps.parcels import OUT_PATH as PARCELS_PATH

log = logging.getLogger(__name__)

OUT_PATH = PROCESSED_DIR / "addresses.parquet"
SUMMARY_PATH = PROCESSED_DIR / "addresses_summary.json"
# An address point a few feet outside every parcel (e.g. on a lot line) is
# matched to the nearest parcel within this distance; farther ones stay unmatched.
NEAREST_MAX_FT = 50.0


def run(cfg: Config, client: PoliteClient, refresh: bool = False) -> dict:
    src = cfg.sources["city_site_addresses"]
    store = RawStore("city_site_addresses")
    arcgis.layer_metadata(client, store, src, refresh)
    features = arcgis.fetch_all(client, store, src, geometry=True, refresh=refresh)

    pts = features_to_gdf(features).rename(columns={v: k for k, v in src.fields.items()})
    pts = pts[pts.geometry.notna() & ~pts.geometry.is_empty]
    pts = pts.to_crs(cfg.city.crs_projected)

    parcels = gpd.read_parquet(PARCELS_PATH)[["parcel_key", "geometry"]].to_crs(cfg.city.crs_projected)

    within = gpd.sjoin(pts, parcels, how="left", predicate="within")
    multi_hit = int(within.index.duplicated().sum())
    within = within[~within.index.duplicated(keep="first")]
    within["match_method"] = within["parcel_key"].notna().map({True: "within", False: None})

    missing = within["parcel_key"].isna()
    if missing.any():
        near = gpd.sjoin_nearest(
            pts.loc[missing[missing].index],
            parcels,
            how="left",
            max_distance=NEAREST_MAX_FT,
            distance_col="dist_ft",
        )
        near = near[~near.index.duplicated(keep="first")]
        within.loc[near.index, "parcel_key"] = near["parcel_key"]
        within.loc[near.index[near["parcel_key"].notna()], "match_method"] = f"nearest_{int(NEAREST_MAX_FT)}ft"

    out = within[["object_id", "full_address", "unit", "zip", "parcel_key", "match_method", "geometry"]].copy()
    out["source_url"] = src.url
    out["retrieved_at"] = store.retrieved_at()
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=cfg.city.crs_projected).to_crs(cfg.city.crs_web)

    summary = {
        "address_points": len(out),
        "matched_within": int((out["match_method"] == "within").sum()),
        "matched_nearest": int(out["match_method"].fillna("").str.startswith("nearest").sum()),
        "unmatched": int(out["parcel_key"].isna().sum()),
        "points_in_overlapping_parcels": multi_hit,
        "retrieved_at": store.retrieved_at(),
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.reset_index(drop=True).to_parquet(OUT_PATH)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info("wrote %s (%d addresses)", OUT_PATH, len(out))
    return summary
