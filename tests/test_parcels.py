"""Parcel-step logic tested on small hand-made shapes (FAKE test data, not real parcels)."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from pipeline.arcgis import coded_value_domains, page_offsets
from pipeline.geo import SQFT_PER_ACRE, close_gaps
from pipeline.steps.parcels import check_layers_agree, merge_parts

CRS = "EPSG:6420"  # US feet


def test_lot_area_of_a_100_by_100_ft_square():
    g = gpd.GeoSeries([box(0, 0, 100, 100)], crs=CRS)
    assert g.area.iloc[0] == pytest.approx(10_000)
    assert g.area.iloc[0] / SQFT_PER_ACRE == pytest.approx(0.2296, abs=1e-4)


def test_merge_parts_unions_pieces_and_keeps_largest_piece_attributes():
    fake = gpd.GeoDataFrame(
        {
            "parcel_key": ["11111111", "11111111", "22222222"],
            "object_id": [1, 2, 3],
            "zoning": ["MUCC", "PD", "R3"],          # pieces of 1111 disagree
            "general_plan": ["CMXU", "CMXU", "MDRE"],
            "specific_plan": ["ECR", "ECR", None],
            "parcel_type": ["LND", "LND", "LND"],
        },
        geometry=[box(0, 0, 100, 100), box(200, 0, 210, 10), box(500, 500, 550, 550)],
        crs=CRS,
    )
    out, multi, conflicts = merge_parts(fake)
    assert len(out) == 2 and multi == 1 and conflicts == 1
    merged = out.set_index("parcel_key").loc["11111111"]
    assert merged["zoning"] == "MUCC"            # from the 10,000 sq ft piece
    assert merged["geometry"].area == pytest.approx(10_000 + 100)
    assert merged["n_parts"] == 2 and sorted(merged["object_ids"]) == [1, 2]


def test_check_layers_agree_passes_and_fails():
    parcels = pd.DataFrame({"object_id": [1, 2, 3], "zoning": ["R3", "PD", None], "specific_plan": [None, "ECR", None], "status": ["A", "A", "R"]})
    same = parcels.copy()
    assert check_layers_agree(parcels, same, 0.0)["attribute_mismatches"] == 0

    different = parcels.copy()
    different.loc[1, "zoning"] = "MUCC"
    with pytest.raises(RuntimeError):
        check_layers_agree(parcels, different, 0.1)
    assert check_layers_agree(parcels, different, 0.5)["attribute_mismatches"] == 1


def test_close_gaps_bridges_a_street_but_not_a_block():
    left, right = box(0, 0, 100, 100), box(180, 0, 280, 100)   # 80 ft "street"
    assert close_gaps([left, right], 60).geom_type == "Polygon"
    far = box(500, 0, 600, 100)                                 # 220 ft gap
    assert close_gaps([left, far], 60).geom_type == "MultiPolygon"


def test_page_offsets_and_domains():
    assert page_offsets(29_971, 5_000) == [0, 5000, 10000, 15000, 20000, 25000]
    assert page_offsets(0, 1000) == []
    meta = {"fields": [{"name": "SPPLAN", "domain": {"type": "codedValue", "codedValues": [{"code": "ECR", "name": "El Camino Real Specific Plan"}]}}, {"name": "APN"}]}
    assert coded_value_domains(meta) == {"SPPLAN": {"ECR": "El Camino Real Specific Plan"}}
