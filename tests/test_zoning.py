import pytest

from pipeline.zoning import (
    FAMILY_LABELS,
    UnmappedZoningCodeError,
    family_for,
    load_family_map,
)


def test_family_map_loads_and_uses_known_families():
    mapping = load_family_map()
    assert set(mapping.values()) <= set(FAMILY_LABELS)
    # Spot checks on codes that drive the demo.
    assert mapping["MUCC"] == "mixed_use"
    assert mapping["PD"] == "planned_dev"
    assert mapping["R1-6L"] == "single_family"
    assert mapping["VHDR"] == "multifamily"


def test_family_for_null_and_unknown():
    mapping = {"R3": "multifamily"}
    assert family_for(None, mapping) == "none"
    assert family_for("", mapping) == "none"
    assert family_for(float("nan"), mapping) == "none"  # how pandas hands over missing values
    with pytest.raises(UnmappedZoningCodeError):
        family_for("XYZ", mapping)

