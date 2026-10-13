"""Loads config/sources.yaml into typed objects and defines repo paths."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
WEB_DATA_DIR = REPO_ROOT / "web" / "public" / "data"


class CityConfig(BaseModel):
    id: str
    name: str
    state: str
    crs_projected: str
    crs_web: str


class HttpConfig(BaseModel):
    user_agent: str
    min_interval_seconds: float
    timeout_seconds: float
    max_attempts: int


class ArcGISSource(BaseModel):
    name: str
    url: str
    attribution: str
    page_size: int
    out_fields: list[str]
    fields: dict[str, str]
    active_status_value: str | None = None
    max_mismatch_share: float | None = None


class Links(BaseModel):
    zoning_code_home: str
    zoning_code_label: str
    general_plan_home: str
    general_plan_label: str


class Config(BaseModel):
    city: CityConfig
    http: HttpConfig
    sources: dict[str, ArcGISSource]
    links: Links


def load_config(path: Path | None = None) -> Config:
    path = path or CONFIG_DIR / "sources.yaml"
    with open(path) as f:
        return Config.model_validate(yaml.safe_load(f))
