"""Step `export`: write the files the web app reads into web/public/data/.

  parcels.geojson       lean map layer: key, zoning family/code, plan, parcel type
  parcel_details.json   what the parcel panel shows, one compact row per parcel
                        ({"fields": [...], "rows": {key: [values...]}}); labels
                        live once in meta.json "lookups" instead of on every row
  search_index.json     [address, parcel key] pairs for address search
  plan_areas.geojson    specific-plan outlines; plan_labels.geojson label points
  meta.json             counts, legend, lookups, sources with retrieval times
"""

from __future__ import annotations

import gzip
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd

from pipeline.config import WEB_DATA_DIR, Config
from pipeline.geo import round_coords
from pipeline.http import PoliteClient
from pipeline.steps.addresses import OUT_PATH as ADDRESSES_PATH
from pipeline.steps.addresses import SUMMARY_PATH as ADDRESSES_SUMMARY
from pipeline.steps.parcels import OUT_PATH as PARCELS_PATH
from pipeline.steps.parcels import SUMMARY_PATH as PARCELS_SUMMARY
from pipeline.steps.plan_areas import OUT_PATH as PLANS_PATH
from pipeline.zoning import FAMILIES

log = logging.getLogger(__name__)

COORD_DIGITS = 6  # ~0.1 m; finer than parcel-line accuracy
SIMPLIFY_FT = 1.0
MAX_PANEL_ADDRESSES = 6

DETAIL_FIELDS = [
    "apn", "is_assessor_apn", "addresses", "address_count", "parcel_type", "zoning", "general_plan",
    "specific_plan", "historic", "flood", "year_built", "lot_area_sqft", "lot_area_acres",
    "acreage_published", "zip", "council_district", "n_parts", "object_ids",
]


def clean(value):
    """pandas/numpy values -> plain JSON values (NA/NaN -> None)."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):  # numpy scalar
        return clean(value.item())
    return value


def write_json(path: Path, obj) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path.write_bytes(data)
    return {"bytes": len(data), "gzip_bytes": len(gzip.compress(data, compresslevel=6))}


def feature(geom, props: dict) -> dict:
    g = geom.__geo_interface__
    return {
        "type": "Feature",
        "properties": props,
        "geometry": {"type": g["type"], "coordinates": round_coords(g["coordinates"], COORD_DIGITS)},
    }


def address_sort_key(address: str) -> tuple[str, int, str]:
    """Sort by street, then house number: '4160 Network Circle' -> ('network circle', 4160, ...)."""
    number, _, street = address.partition(" ")
    return (street.lower(), int(number) if number.isdigit() else 0, address)


def lookup(df: pd.DataFrame, code_col: str, label_col: str) -> dict[str, str]:
    pairs = df[[code_col, label_col]].dropna(subset=[code_col]).drop_duplicates(code_col)
    return {str(c): clean(lbl) or str(c) for c, lbl in zip(pairs[code_col], pairs[label_col])}


def run(cfg: Config, client: PoliteClient | None = None, refresh: bool = False) -> dict:
    parcels = gpd.read_parquet(PARCELS_PATH)
    addresses = gpd.read_parquet(ADDRESSES_PATH)
    plans = gpd.read_parquet(PLANS_PATH)
    parcels_summary = json.loads(PARCELS_SUMMARY.read_text())
    addresses_summary = json.loads(ADDRESSES_SUMMARY.read_text())
    sizes: dict[str, dict] = {}

    # Map layer: shapes simplified by 1 ft (invisible at map scale) to cut file size.
    simple = parcels.to_crs(cfg.city.crs_projected)
    simple["geometry"] = simple.geometry.simplify(SIMPLIFY_FT, preserve_topology=True)
    simple = simple.to_crs(cfg.city.crs_web)
    map_features = [
        feature(
            row.geometry,
            {
                "k": row.parcel_key,
                "f": row.zoning_family,
                "z": clean(row.zoning) or "",
                "sp": clean(row.specific_plan) or "",
                "t": clean(row.parcel_type) or "",
            },
        )
        for row in simple.itertuples()
    ]
    sizes["parcels.geojson"] = write_json(WEB_DATA_DIR / "parcels.geojson", {"type": "FeatureCollection", "features": map_features})

    matched = addresses[addresses["parcel_key"].notna() & addresses["full_address"].notna()]
    addr_by_key = (
        matched.drop_duplicates(["parcel_key", "full_address"])
        .groupby("parcel_key")["full_address"]
        .apply(lambda s: sorted(s, key=address_sort_key))
        .to_dict()
    )

    rows = {}
    for r in parcels.itertuples():
        addrs = addr_by_key.get(r.parcel_key, [])
        rows[r.parcel_key] = [
            r.apn_display, bool(r.is_assessor_apn), addrs[:MAX_PANEL_ADDRESSES], len(addrs),
            clean(r.parcel_type), clean(r.zoning), clean(r.general_plan), clean(r.specific_plan),
            clean(r.historic_type), clean(r.flood_note), clean(r.year_built), clean(r.lot_area_sqft),
            clean(r.lot_area_acres), clean(r.acreage_published), clean(r.zip), clean(r.council_district),
            clean(r.n_parts), [int(x) for x in r.object_ids],
        ]
    sizes["parcel_details.json"] = write_json(WEB_DATA_DIR / "parcel_details.json", {"fields": DETAIL_FIELDS, "rows": rows})

    search = sorted({(a, k) for a, k in zip(matched["full_address"], matched["parcel_key"])})
    sizes["search_index.json"] = write_json(WEB_DATA_DIR / "search_index.json", [list(x) for x in search])

    plan_features = [
        feature(p.geometry, {"code": p.code, "label": p.label, "parcels": clean(p.parcel_count), "acres": clean(p.parcel_acres)})
        for p in plans.itertuples()
    ]
    label_features = [
        {"type": "Feature", "properties": {"code": p.code, "label": p.label}, "geometry": {"type": "Point", "coordinates": [p.label_lon, p.label_lat]}}
        for p in plans.itertuples()
    ]
    sizes["plan_areas.geojson"] = write_json(WEB_DATA_DIR / "plan_areas.geojson", {"type": "FeatureCollection", "features": plan_features})
    sizes["plan_labels.geojson"] = write_json(WEB_DATA_DIR / "plan_labels.geojson", {"type": "FeatureCollection", "features": label_features})

    zoning_pairs = parcels[["zoning", "zoning_label", "zoning_family"]].dropna(subset=["zoning"]).drop_duplicates("zoning")
    family_counts = parcels["zoning_family"].value_counts().to_dict()
    lp_src, z_src, a_src = (cfg.sources[k] for k in ("city_land_parcels", "city_zoning", "city_site_addresses"))
    meta = {
        "product": "SoftSite",
        "city": f"{cfg.city.name}, {cfg.city.state}",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bounds": [round(float(v), 5) for v in parcels.total_bounds],
        "counts": {
            "parcels_mapped": len(parcels),
            "land_parcels": int((parcels["parcel_type"] == "LND").sum()),
            "addresses_indexed": len(search),
        },
        "families": [{"code": c, "label": lbl, "count": int(family_counts.get(c, 0))} for c, lbl in FAMILIES],
        "plans": [
            {"code": p.code, "label": p.label, "parcel_count": clean(p.parcel_count), "parcel_acres": clean(p.parcel_acres)}
            for p in plans.sort_values("label").itertuples()
        ],
        "lookups": {
            "parcel_type": lookup(parcels, "parcel_type", "parcel_type_label"),
            "zoning": {z: {"label": clean(lbl) or z, "family": fam} for z, lbl, fam in zoning_pairs.itertuples(index=False)},
            "general_plan": lookup(parcels, "general_plan", "general_plan_label"),
            "specific_plan": lookup(parcels, "specific_plan", "specific_plan_label"),
            "historic": lookup(parcels, "historic_type", "historic_label"),
            "flood": lookup(parcels, "flood_note", "flood_label"),
        },
        "sources": [
            {
                "id": "city_land_parcels",
                "name": lp_src.name,
                "url": lp_src.url,
                "attribution": lp_src.attribution,
                "retrieved_at": parcels_summary["retrieved_at"]["land_parcels"],
                "records": parcels_summary["source_features"],
            },
            {
                "id": "city_zoning",
                "name": z_src.name,
                "url": z_src.url,
                "attribution": z_src.attribution,
                "retrieved_at": parcels_summary["retrieved_at"]["zoning"],
                "records": parcels_summary["layer_agreement"]["zoning_records"],
            },
            {
                "id": "city_site_addresses",
                "name": a_src.name,
                "url": a_src.url,
                "attribution": a_src.attribution,
                "retrieved_at": addresses_summary["retrieved_at"],
                "records": addresses_summary["address_points"],
            },
        ],
        "links": cfg.links.model_dump(),
    }
    sizes["meta.json"] = write_json(WEB_DATA_DIR / "meta.json", meta)
    log.info("export sizes: %s", sizes)
    return {"sizes": sizes, "counts": meta["counts"]}
