"""Zoning families: a display grouping of zoning codes for the map legend.

This is NOT used to compute capacity; Phase 2's config/zoning_rules.csv does
that, with citations. Families only decide map colors and filters."""

from __future__ import annotations

import csv
from pathlib import Path

from pipeline.config import CONFIG_DIR

# Display order and labels for the legend.
FAMILIES: list[tuple[str, str]] = [
    ("single_family", "Single-family residential"),
    ("low_density_res", "Duplex / low-density residential"),
    ("multifamily", "Multifamily residential"),
    ("mixed_use", "Mixed use"),
    ("commercial", "Commercial"),
    ("office_rd", "Office / R&D"),
    ("industrial", "Industrial"),
    ("planned_dev", "Planned development (PD)"),
    ("public_open", "Public / open space"),
    ("none", "No zoning in City GIS"),
]
FAMILY_LABELS = dict(FAMILIES)


class UnmappedZoningCodeError(RuntimeError):
    pass


def load_family_map(path: Path | None = None) -> dict[str, str]:
    path = path or CONFIG_DIR / "zoning_families.csv"
    mapping: dict[str, str] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            code, family = row["code"].strip(), row["family"].strip()
            if family not in FAMILY_LABELS:
                raise ValueError(f"{path.name}: unknown family {family!r} for code {code!r}")
            if code in mapping:
                raise ValueError(f"{path.name}: duplicate code {code!r}")
            mapping[code] = family
    return mapping


def family_for(code: str | None, mapping: dict[str, str]) -> str:
    if code is None or code == "" or code != code:  # code != code catches NaN
        return "none"
    try:
        return mapping[code]
    except KeyError:
        raise UnmappedZoningCodeError(
            f"Zoning code {code!r} appears in the data but not in config/zoning_families.csv. "
            "Add it with a family before rerunning."
        ) from None

