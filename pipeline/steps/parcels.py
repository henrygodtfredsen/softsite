"""Step `parcels`: pull the City's Land Parcels and Zoning layers, join them,
keep active parcels, merge multi-part parcels by APN, compute lot area, and
write data/processed/parcels.parquet (WGS84)."""

from __future__ import annotations

import json
import logging

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

from pipeline import arcgis
from pipeline.apn import format_apn, normalize_apn
from pipeline.config import PROCESSED_DIR, Config
from pipeline.geo import SQFT_PER_ACRE, features_to_gdf
from pipeline.http import PoliteClient
from pipeline.raw_store import RawStore
from pipeline.zoning import FAMILY_LABELS, family_for, load_family_map

log = logging.getLogger(__name__)

OUT_PATH = PROCESSED_DIR / "parcels.parquet"
SUMMARY_PATH = PROCESSED_DIR / "parcels_summary.json"
COMPARED_FIELDS = ["zoning", "specific_plan", "status"]
ATTRIBUTE_FIELDS = ["zoning", "general_plan", "specific_plan", "parcel_type"]


def _rename(df: pd.DataFrame, fields: dict[str, str]) -> pd.DataFrame:
    return df.rename(columns={source: ours for ours, source in fields.items()})


def check_layers_agree(parcels: pd.DataFrame, zoning: pd.DataFrame, max_share: float) -> dict:
    """The Zoning layer has no APN, so it is joined on OBJECTID. That is only
    safe if both layers are views of the same records: same OBJECTIDs, same
    zoning / plan / status on each. Abort if more than `max_share` disagree."""
    a = parcels.set_index("object_id")[COMPARED_FIELDS].fillna("<null>")
    b = zoning.set_index("object_id")[COMPARED_FIELDS].fillna("<null>")
    only_parcels = a.index.difference(b.index)
    only_zoning = b.index.difference(a.index)
    common = a.index.intersection(b.index)
    mismatched = (a.loc[common] != b.loc[common]).any(axis=1)
    n_bad = int(mismatched.sum()) + len(only_parcels)
    share = n_bad / max(len(a), 1)
    result = {
        "parcel_records": len(a),
        "zoning_records": len(b),
        "only_in_parcels": len(only_parcels),
        "only_in_zoning": len(only_zoning),
        "attribute_mismatches": int(mismatched.sum()),
        "mismatch_share": round(share, 6),
        "examples": [int(x) for x in list(common[mismatched.to_numpy()][:5]) + list(only_parcels[:5])],
    }
    if share > max_share:
        raise RuntimeError(
            f"Land Parcels and Zoning layers disagree on {share:.2%} of records "
            f"(limit {max_share:.2%}): {result}. The OBJECTID join may no longer be safe."
        )
    return result


def merge_parts(proj: gpd.GeoDataFrame, key: str = "parcel_key") -> tuple[gpd.GeoDataFrame, int, int]:
    """One row per parcel. A parcel stored as several polygons is unioned; its
    attributes come from the largest piece. Returns (rows, multi-part parcels,
    parcels whose pieces disagree on zoning / GP / plan / type)."""
    proj = proj.assign(_area=proj.geometry.area).sort_values([key, "_area"], ascending=[True, False])
    dup = proj[key].duplicated(keep=False)
    singles = proj[~dup].assign(n_parts=1, object_ids=lambda d: d["object_id"].map(lambda x: [int(x)]))

    multis = proj[dup]
    conflicts = 0
    merged_rows = []
    for _, grp in multis.groupby(key, sort=False):
        first = grp.iloc[0].copy()
        if (grp[ATTRIBUTE_FIELDS].fillna("<null>").nunique() > 1).any():
            conflicts += 1
        first["geometry"] = unary_union(list(grp.geometry))
        first["n_parts"] = len(grp)
        first["object_ids"] = [int(x) for x in grp["object_id"]]
        merged_rows.append(first)
    merged = gpd.GeoDataFrame(merged_rows, geometry="geometry", crs=proj.crs) if merged_rows else proj.iloc[:0]

    out = pd.concat([singles, merged], ignore_index=True).drop(columns="_area")
    return gpd.GeoDataFrame(out, geometry="geometry", crs=proj.crs), multis[key].nunique(), conflicts


def run(cfg: Config, client: PoliteClient, refresh: bool = False) -> dict:
    lp_src = cfg.sources["city_land_parcels"]
    z_src = cfg.sources["city_zoning"]
    lp_store = RawStore("city_land_parcels")
    z_store = RawStore("city_zoning")

    lp_meta = arcgis.layer_metadata(client, lp_store, lp_src, refresh)
    z_meta = arcgis.layer_metadata(client, z_store, z_src, refresh)
    lp_features = arcgis.fetch_all(client, lp_store, lp_src, geometry=True, refresh=refresh)
    z_features = arcgis.fetch_all(client, z_store, z_src, geometry=False, refresh=refresh)

    domains = {**arcgis.coded_value_domains(z_meta), **arcgis.coded_value_domains(lp_meta)}

    def label(field_key: str, src_fields: dict[str, str], code) -> str | None:
        if code is None or pd.isna(code):
            return None
        return domains.get(src_fields[field_key], {}).get(str(code))

    gdf = _rename(features_to_gdf(lp_features), lp_src.fields)
    zdf = _rename(pd.DataFrame([f["properties"] for f in z_features]), z_src.fields)
    agreement = check_layers_agree(gdf, zdf, z_src.max_mismatch_share or 0.0)

    gdf = gdf.merge(zdf[["object_id", "flood_note", "zoning_url", "general_plan_url"]], on="object_id", how="left")

    summary: dict = {"source_features": len(gdf), "layer_agreement": agreement}
    gdf = gdf[gdf["status"] == lp_src.active_status_value].copy()
    summary["active_features"] = len(gdf)

    no_geom = gdf.geometry.isna() | gdf.geometry.is_empty
    summary["dropped_no_geometry"] = int(no_geom.sum())
    gdf = gdf[~no_geom]

    # Real assessor APNs become the parcel key. Some condo common areas carry a
    # City-only ID with a letter suffix (e.g. 097-90-00A) that is not an
    # assessor APN: they stay on the map under that City ID, are logged, and
    # can never join to County or State data.
    gdf["apn_raw"] = gdf["apn"].map(lambda v: v.strip() if isinstance(v, str) else None)
    gdf["apn"] = gdf["apn_raw"].map(normalize_apn)
    no_id = gdf["apn_raw"].isna() | (gdf["apn_raw"] == "")
    summary["dropped_no_parcel_id"] = int(no_id.sum())
    gdf = gdf[~no_id]
    city_id_only = gdf["apn"].isna()
    summary["kept_with_city_id_not_apn"] = gdf.loc[city_id_only, "parcel_type"].value_counts().to_dict()
    if city_id_only.any():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        gdf.loc[city_id_only, ["object_id", "apn_raw", "parcel_type"]].assign(
            source=lp_src.name, handling="kept on map under City ID; not an assessor APN"
        ).to_csv(PROCESSED_DIR / "unmatched_apns.csv", index=False)
    gdf["parcel_key"] = gdf["apn"].where(~city_id_only, "CITY-" + gdf["apn_raw"])

    proj = gdf.to_crs(cfg.city.crs_projected)
    invalid = ~proj.geometry.is_valid
    summary["repaired_invalid_geometry"] = int(invalid.sum())
    proj.loc[invalid, "geometry"] = proj.loc[invalid, "geometry"].make_valid()

    proj, multi_part, conflicts = merge_parts(proj)
    summary["multi_part_parcels_merged"] = int(multi_part)
    summary["multi_part_attribute_conflicts"] = int(conflicts)

    proj["lot_area_sqft"] = proj.geometry.area.round(0)
    proj["lot_area_acres"] = (proj["lot_area_sqft"] / SQFT_PER_ACRE).round(3)

    family_map = load_family_map()
    unmapped = sorted({c for c in proj["zoning"].dropna().unique() if c not in family_map})
    if unmapped:
        raise RuntimeError(f"Zoning codes missing from config/zoning_families.csv: {unmapped}")

    lp_f, z_f = lp_src.fields, z_src.fields
    proj["is_assessor_apn"] = proj["apn"].notna()
    proj["apn_display"] = [format_apn(a) if isinstance(a, str) else raw for a, raw in zip(proj["apn"], proj["apn_raw"])]
    proj["zoning_family"] = proj["zoning"].map(lambda c: family_for(c, family_map))
    proj["zoning_family_label"] = proj["zoning_family"].map(FAMILY_LABELS)
    proj["zoning_label"] = proj["zoning"].map(lambda c: label("zoning", lp_f, c))
    proj["general_plan_label"] = proj["general_plan"].map(lambda c: label("general_plan", lp_f, c))
    proj["specific_plan_label"] = proj["specific_plan"].map(lambda c: label("specific_plan", lp_f, c))
    proj["historic_label"] = proj["historic_type"].map(lambda c: label("historic_type", lp_f, c))
    proj["parcel_type_label"] = proj["parcel_type"].map(lambda c: label("parcel_type", lp_f, c))
    proj["flood_label"] = proj["flood_note"].map(lambda c: label("flood_note", z_f, c))
    proj["year_built"] = pd.to_numeric(proj["year_built"], errors="coerce").astype("Int64")
    proj["zip"] = pd.to_numeric(proj["zip"], errors="coerce").astype("Int64").replace(0, pd.NA)

    proj["source_name"] = lp_src.name
    proj["source_url"] = lp_src.url
    proj["retrieved_at"] = lp_store.retrieved_at()
    proj["zoning_layer_url"] = z_src.url
    proj["zoning_layer_retrieved_at"] = z_store.retrieved_at()

    # zoning_url / general_plan_url are kept for transparency but NOT shown in
    # the app: the City's per-parcel links are inconsistent (e.g. R3 parcels
    # point at 16 different code chapters). See docs/DATA_SOURCES.md.
    keep = [
        "parcel_key", "apn", "is_assessor_apn", "apn_display", "object_ids", "n_parts", "parcel_type", "parcel_type_label",
        "zoning", "zoning_label", "zoning_family", "zoning_family_label", "zoning_url",
        "general_plan", "general_plan_label", "general_plan_url",
        "specific_plan", "specific_plan_label", "historic_type", "historic_label",
        "flood_note", "flood_label", "year_built", "acreage_published", "lot_area_sqft", "lot_area_acres",
        "zip", "council_district", "source_name", "source_url", "retrieved_at",
        "zoning_layer_url", "zoning_layer_retrieved_at", "geometry",
    ]
    out = proj[keep].to_crs(cfg.city.crs_web).sort_values("parcel_key").reset_index(drop=True)

    summary.update(
        {
            "parcels_out": len(out),
            "by_parcel_type": out["parcel_type"].value_counts(dropna=False).to_dict(),
            "by_family": out["zoning_family"].value_counts().to_dict(),
            "by_specific_plan": out["specific_plan"].fillna("none").value_counts().to_dict(),
            "retrieved_at": {"land_parcels": lp_store.retrieved_at(), "zoning": z_store.retrieved_at()},
        }
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info("wrote %s (%d parcels)", OUT_PATH, len(out))
    return summary
