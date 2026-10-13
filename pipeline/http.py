"""A polite HTTP client: one identified User-Agent, a minimum gap between
requests, retries with exponential backoff, and loud failures when a site's
bot protection answers instead of the data service."""

from __future__ import annotations

import logging
import time

import httpx

from pipeline.config import HttpConfig

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class SourceBlockedError(RuntimeError):
    """The server answered with a block page (bot protection), not data."""


class ArcGISError(RuntimeError):
    """An ArcGIS REST service returned an error object."""


class PoliteClient:
    def __init__(self, cfg: HttpConfig):
        self._cfg = cfg
        self._client = httpx.Client(
            headers={"User-Agent": cfg.user_agent, "Accept": "application/json"},
            timeout=cfg.timeout_seconds,
            follow_redirects=True,
        )
        self._last_request = 0.0

    def _wait_turn(self) -> None:
        gap = time.monotonic() - self._last_request
        if gap < self._cfg.min_interval_seconds:
            time.sleep(self._cfg.min_interval_seconds - gap)

    def get_json(self, url: str, params: dict | None = None) -> dict:
        last_error: Exception | None = None
        for attempt in range(1, self._cfg.max_attempts + 1):
            self._wait_turn()
            try:
                resp = self._client.get(url, params=params)
            except httpx.TransportError as exc:
                last_error = exc
                log.warning("network error on %s (attempt %d): %s", url, attempt, exc)
                time.sleep(2**attempt)
                continue
            finally:
                self._last_request = time.monotonic()

            if resp.status_code in RETRYABLE_STATUS:
                last_error = RuntimeError(f"HTTP {resp.status_code}")
                log.warning("HTTP %d on %s (attempt %d)", resp.status_code, url, attempt)
                time.sleep(2**attempt)
                continue

            content_type = resp.headers.get("content-type", "")
            if resp.status_code == 403 or "html" in content_type:
                raise SourceBlockedError(
                    f"{url} answered HTTP {resp.status_code} ({content_type}) instead of data. "
                    "This is usually bot protection. Not retrying; see docs/DATA_SOURCES.md."
                )
            resp.raise_for_status()

            data = resp.json()
            if isinstance(data, dict) and "error" in data:
                raise ArcGISError(f"{url} returned an error: {data['error']}")
            return data

        raise RuntimeError(f"Gave up on {url} after {self._cfg.max_attempts} attempts: {last_error}")

    def close(self) -> None:
        self._client.close()
