"""Minimal read-only client for the public Kalshi Trade API v2.

No API key is needed for market data. Responses are cached on disk so that
notebooks can be rerun without hitting the API again.
"""
import hashlib
import json
import threading
import time
from pathlib import Path

import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "cache"
MIN_INTERVAL = 0.1  # seconds between requests (about 10 requests per second)

_session = requests.Session()
_last_call = 0.0
_lock = threading.Lock()  # shared throttle, so parallel workers respect the rate limit


def get(path, params=None, use_cache=True, retries=5):
    """GET a Kalshi endpoint and return the decoded JSON, with caching and retries."""
    global _last_call
    params = {k: v for k, v in (params or {}).items() if v is not None}
    key = hashlib.sha1(json.dumps([path, params], sort_keys=True).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text())

    for attempt in range(retries):
        with _lock:
            wait = MIN_INTERVAL - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            _last_call = time.time()
        resp = _session.get(BASE_URL + path, params=params, timeout=60)
        if resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(2 ** attempt)  # rate limited or server error: back off
            continue
        resp.raise_for_status()
        data = resp.json()
        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data))
        return data
    raise RuntimeError(f"Kalshi API still failing after {retries} attempts: {path} {params}")


def paginate(path, key, params=None, use_cache=True, max_pages=None):
    """Iterate over every item of a cursor-paginated endpoint."""
    params = dict(params or {})
    page = 0
    while True:
        data = get(path, params, use_cache=use_cache)
        yield from data.get(key, [])
        page += 1
        cursor = data.get("cursor")
        if not cursor or (max_pages and page >= max_pages):
            return
        params["cursor"] = cursor


def historical_cutoff():
    """Timestamps separating the live tier from the historical tier."""
    return get("/historical/cutoff", use_cache=False)


def list_series(include_volume=True):
    return get("/series", {"include_volume": str(include_volume).lower()})["series"]


def settled_markets(series_ticker):
    """All settled, non-combo markets of a series, from both data tiers."""
    # Filters on /historical/markets are mutually exclusive, so no mve_filter here.
    # A regular series holds no combo markets anyway.
    params = {"series_ticker": series_ticker, "limit": 1000}
    historical = [{**m, "tier": "historical"} for m in paginate("/historical/markets", "markets", params)]
    live = [{**m, "tier": "live"} for m in paginate("/markets", "markets", {**params, "status": "settled"})]
    seen = {m["ticker"] for m in historical}
    return historical + [m for m in live if m["ticker"] not in seen]


def candlesticks(market, start_ts, end_ts, period_interval):
    """Raw candlesticks of one market. period_interval in minutes: 1, 60 or 1440.

    Archived markets and recent markets are served by different endpoints.
    """
    params = {"start_ts": int(start_ts), "end_ts": int(end_ts), "period_interval": period_interval}
    if market["tier"] == "historical":
        path = f"/historical/markets/{market['ticker']}/candlesticks"
    else:
        path = f"/series/{market['series_ticker']}/markets/{market['ticker']}/candlesticks"
    return get(path, params).get("candlesticks", [])
