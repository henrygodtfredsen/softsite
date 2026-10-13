"""Step `plan_areas`: build an outline for each specific-plan / focus area by
merging its parcels and closing the street gaps between them. The City
publishes plan membership per parcel (SPPLAN), not plan boundaries, so these
outlines are derived. Writes data/processed/plan_areas.parquet (WGS84)."""

from __future__ import annotations

import logging

import geopandas as gpd

from pipeline.config import PROCESSED_DIR, Config
from pipeline.geo import close_gaps
from pipeline.http import PoliteClient
from pipeline.steps.parcels import OUT_PATH as PARCELS_PATH

log = logging.getLogger(__name__)

OUT_PATH = PROCESSED_DIR / "plan_areas.parquet"
# Streets up to ~120 ft wide (El Camino Real's right-of-way) are bridged.
GAP_CLOSE_FT = 60.0
SIMPLIFY_FT = 5.0


def run(cfg: Config, client: PoliteClient | None = None, refresh: bool = False) -> dict:
    parcels = gpd.read_parquet(PARCELS_PATH)
    parcels = parcels[parcels["specific_plan"].notna()].to_crs(cfg.city.crs_projected)

    rows = []
    for code, grp in parcels.groupby("specific_plan"):
        outline = close_gaps(list(grp.geometry), GAP_CLOSE_FT).simplify(SIMPLIFY_FT, preserve_topology=True)
        largest = max(getattr(outline, "geoms", [outline]), key=lambda g: g.area)
        rows.append(
            {
                "code": code,
                "label": grp["specific_plan_label"].iloc[0],
                "parcel_count": len(grp),
                "land_parcel_count": int((grp["parcel_type"] == "LND").sum()),
                "parcel_acres": round(float(grp["lot_area_acres"].sum()), 1),
                "label_point": largest.representative_point(),
                "geometry": outline,
            }
        )
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=cfg.city.crs_projected)
    label_pts = gpd.GeoSeries(gdf["label_point"], crs=cfg.city.crs_projected).to_crs(cfg.city.crs_web)
    gdf = gdf.drop(columns="label_point").to_crs(cfg.city.crs_web)
    gdf["label_lon"] = label_pts.x.round(6)
    gdf["label_lat"] = label_pts.y.round(6)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(OUT_PATH)
    log.info("wrote %s (%d plan areas)", OUT_PATH, len(gdf))
    return {"plan_areas": gdf[["code", "label", "parcel_count", "parcel_acres"]].to_dict("records")}
