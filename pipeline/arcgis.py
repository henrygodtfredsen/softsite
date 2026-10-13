"""Reads ArcGIS REST map-service layers: layer metadata, coded-value domains,
and complete record sets pulled in pages.

The City's server sits behind a firewall that blocks SQL-looking filters, so
every query asks for all records (`where=1=1`) and filtering happens locally."""

from __future__ import annotations

import logging

from pipeline.config import ArcGISSource
from pipeline.http import PoliteClient
from pipeline.raw_store import RawStore

log = logging.getLogger(__name__)


def layer_metadata(client: PoliteClient, store: RawStore, src: ArcGISSource, refresh: bool) -> dict:
    cached = None if refresh else store.load("layer")
    if cached is not None:
        return cached
    params = {"f": "json"}
    meta = client.get_json(src.url, params)
    store.save("layer", meta, src.url, params)
    return meta


def coded_value_domains(meta: dict) -> dict[str, dict[str, str]]:
    """Field name -> {code: label} for every field with a coded-value domain."""
    domains: dict[str, dict[str, str]] = {}
    for field in meta.get("fields", []):
        domain = field.get("domain") or {}
        if domain.get("type") == "codedValue":
            domains[field["name"]] = {str(c["code"]): c["name"] for c in domain["codedValues"]}
    return domains


def page_offsets(total: int, page_size: int) -> list[int]:
    return list(range(0, total, page_size)) if total > 0 else []


def fetch_all(
    client: PoliteClient,
    store: RawStore,
    src: ArcGISSource,
    *,
    geometry: bool,
    refresh: bool,
) -> list[dict]:
    """Every record in the layer, as GeoJSON-like features
    ({"properties": {...}, "geometry": {...} or None}), in OBJECTID order.
    Geometry is requested in WGS84 (EPSG:4326)."""
    query_url = f"{src.url}/query"

    count_params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    count_resp = None if refresh else store.load("count")
    if count_resp is None:
        count_resp = client.get_json(query_url, count_params)
        store.save("count", count_resp, query_url, count_params)
    total = int(count_resp["count"])

    features: list[dict] = []
    for i, offset in enumerate(page_offsets(total, src.page_size)):
        name = f"page_{i:04d}"
        params = {
            "where": "1=1",
            "outFields": ",".join(src.out_fields),
            "orderByFields": "OBJECTID ASC",
            "resultOffset": offset,
            "resultRecordCount": src.page_size,
            "returnGeometry": "true" if geometry else "false",
            "f": "geojson" if geometry else "json",
        }
        if geometry:
            params["outSR"] = 4326
        page = None if refresh else store.load(name)
        if page is None:
            log.info("%s: fetching records %d-%d of %d", src.name, offset, offset + src.page_size, total)
            page = client.get_json(query_url, params)
            store.save(name, page, query_url, params)
        if geometry:
            features.extend(page["features"])
        else:
            features.extend({"properties": f["attributes"], "geometry": None} for f in page["features"])

    if len(features) != total:
        raise RuntimeError(
            f"{src.name}: service reported {total} records but {len(features)} were returned. "
            "The layer may have changed mid-download; rerun with --refresh."
        )
    return features
