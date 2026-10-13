"""Small geometry helpers. Measurements are done in the projected CRS from
config (US feet); only the final web export is converted to lat/long."""

from __future__ import annotations

import geopandas as gpd
from shapely import Geometry
from shapely.ops import unary_union

SQFT_PER_ACRE = 43_560.0


def features_to_gdf(features: list[dict], crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame.from_features(features, crs=crs)


def close_gaps(geoms: list[Geometry], distance_ft: float) -> Geometry:
    """Merge parcel shapes into one outline, closing street gaps narrower
    than 2 × distance_ft (a buffer out, then back in)."""
    return unary_union([g.buffer(distance_ft) for g in geoms]).buffer(-distance_ft)


def round_coords(obj, ndigits: int):
    """Round every coordinate in a GeoJSON geometry mapping."""
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, ndigits) for v in obj]
        return [round_coords(o, ndigits) for o in obj]
    return obj
