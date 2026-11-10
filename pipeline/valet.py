"""Minimal client for the Bank of Canada Valet API (no key required).

One run makes exactly one observations request for all series.
"""

import json
import time
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://www.bankofcanada.ca/valet"
USER_AGENT = "rates-fx-monitor/1.0 (portfolio demo; one request per day)"


def fetch_observations(series_ids, start_date: date, timeout=30, retries=3, backoff=2.0) -> dict:
    """Fetch daily observations for all series in a single request.

    Retries timeouts, network errors, 429 and 5xx with exponential backoff
    (2s, 4s, ...). Other 4xx errors (for example an unknown series) fail at once.
    """
    url = f"{BASE_URL}/observations/{','.join(series_ids)}/json?start_date={start_date.isoformat()}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as err:
            retryable = err.code == 429 or err.code >= 500
            if not retryable or attempt == retries:
                body = err.read().decode("utf-8", "replace")[:300]
                raise RuntimeError(f"Valet API returned HTTP {err.code}: {body}") from err
        except (URLError, TimeoutError) as err:
            if attempt == retries:
                raise RuntimeError(f"Valet API unreachable after {retries} attempts: {err}") from err
        time.sleep(backoff * 2 ** (attempt - 1))
    raise AssertionError("unreachable")


def parse_observations(payload: dict, series_ids) -> list[tuple]:
    """Flatten the Valet payload into (series, date, value) rows.

    A series key missing on a date produces no row (a missing day).
    A key that is present with an empty or non-numeric value produces a NULL value.
    """
    rows = []
    for obs in payload.get("observations", []):
        day = date.fromisoformat(obs["d"])
        for series_id in series_ids:
            if series_id not in obs:
                continue
            raw = obs[series_id].get("v")
            try:
                value = float(raw)
            except (TypeError, ValueError):
                value = None
            rows.append((series_id, day, value))
    return rows
