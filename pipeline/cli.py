"""Command line entry point: `uv run pipeline <step> [--refresh]`.

Steps run in this order for `all`: parcels → addresses → plan_areas → export.
Raw responses fetched today are reused unless --refresh is given."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from pipeline.config import load_config
from pipeline.http import PoliteClient
from pipeline.steps import addresses, export, parcels, plan_areas

STEPS = {
    "parcels": parcels.run,
    "addresses": addresses.run,
    "plan_areas": plan_areas.run,
    "export": export.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline", description="SoftSite data pipeline")
    parser.add_argument("step", choices=[*STEPS, "all"])
    parser.add_argument("--refresh", action="store_true", help="re-download even if today's raw data exists")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # our own logs already name each fetch
    cfg = load_config()
    client = PoliteClient(cfg.http)
    try:
        for name in STEPS if args.step == "all" else [args.step]:
            summary = STEPS[name](cfg, client, refresh=args.refresh)
            print(f"\n== {name} ==\n{json.dumps(summary, indent=2, default=str)}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
