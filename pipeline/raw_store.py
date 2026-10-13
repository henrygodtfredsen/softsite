"""Saves every raw API response under data/raw/<source>/<YYYY-MM-DD>/ with a
fetch log (URL, parameters, timestamp), so each processed number can be traced
back to the exact response it came from."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.config import RAW_DIR


class RawStore:
    def __init__(self, source_id: str, run_date: date | None = None, root: Path = RAW_DIR):
        self.source_id = source_id
        self.run_date = run_date or date.today()
        self.dir = root / source_id / self.run_date.isoformat()
        self._log_path = self.dir / "_fetch_log.jsonl"

    def load(self, name: str) -> dict | None:
        path = self.dir / f"{name}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def save(self, name: str, data: dict, url: str, params: dict | None) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.dir / f"{name}.json", "w") as f:
            json.dump(data, f)
        entry = {
            "name": name,
            "url": url,
            "params": params or {},
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def retrieved_at(self) -> str | None:
        """Timestamp of the earliest fetch in this snapshot."""
        if not self._log_path.exists():
            return None
        with open(self._log_path) as f:
            stamps = [json.loads(line)["retrieved_at"] for line in f if line.strip()]
        return min(stamps) if stamps else None
