"""Turn settled Kalshi markets into calibration observations.

One observation = one market at one horizon: the Yes price at (close - horizon),
the volume traded before that time, and the 0/1 outcome.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

from pmcal import kalshi

HOUR, DAY = 3600, 86400
HOURLY_WINDOW = 8 * DAY  # hourly candles cover the last 8 days (API limit on candle count)
MAX_SPREAD = 0.10        # above this, the midpoint is not trusted
FRESHNESS = DAY          # a last trade older than this is not a price

HORIZONS = {"1h": HOUR, "1d": DAY, "7d": 7 * DAY, "30d": 30 * DAY}
HORIZONS_BY_FAMILY = {
    "sports": ["1d", "7d"],          # T-1h would fall during the game
    "weather": ["1h", "1d"],         # markets open about 38 hours before closing
    "politics": ["1h", "1d", "7d", "30d"],
    "economics": ["1h", "1d", "7d", "30d"],
    "crypto": ["1h", "1d", "7d", "30d"],
    "culture": ["1h", "1d", "7d", "30d"],
}


def _ts(col):
    """ISO timestamps (with or without microseconds) to Unix seconds."""
    dt = pd.to_datetime(col, format="ISO8601", utc=True, errors="coerce")
    return (dt - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)


def markets_table(series_row):
    """Settled markets of one series, as a DataFrame with parsed fields."""
    raw = kalshi.settled_markets(series_row["ticker"])
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw)
    out = pd.DataFrame({
        "ticker": df["ticker"],
        "event_ticker": df["event_ticker"],
        "series_ticker": series_row["ticker"],
        "family": series_row["family"],
        "tier": df["tier"],
        "result": df["result"],
        "open_ts": _ts(df["open_time"]),
        "close_ts": _ts(df["close_time"]),
        "expected_expiration_ts": _ts(df["expected_expiration_time"]),
        "lifetime_volume": pd.to_numeric(df["volume_fp"], errors="coerce"),
    })
    return out


def _num(d, *keys):
    """First numeric value found under any of the keys (archive and live use different names)."""
    for k in keys:
        v = d.get(k) if d else None
        if v not in (None, ""):
            return float(v)
    return np.nan


def normalize_candles(raw):
    rows = []
    for c in raw:
        price, bid, ask = c.get("price") or {}, c.get("yes_bid") or {}, c.get("yes_ask") or {}
        rows.append({
            "end_ts": int(c["end_period_ts"]),
            "bid": _num(bid, "close", "close_dollars"),
            "ask": _num(ask, "close", "close_dollars"),
            "last": _num(price, "close", "close_dollars"),
            "volume": _num(c, "volume", "volume_fp"),
        })
    return pd.DataFrame(rows, columns=["end_ts", "bid", "ask", "last", "volume"])


def fetch_candles(m):
    """Hourly candles over the last 8 days, plus daily candles when the market lived longer."""
    hourly_start = max(m["open_ts"], m["close_ts"] - HOURLY_WINDOW)
    hourly = normalize_candles(kalshi.candlesticks(m, hourly_start, m["close_ts"], 60))
    daily = pd.DataFrame(columns=hourly.columns)
    if m["open_ts"] < hourly_start:
        daily = normalize_candles(kalshi.candlesticks(m, m["open_ts"], m["close_ts"], 1440))
    return hourly, daily


def volume_before(t, hourly, daily):
    """Contracts traded up to time t: daily candles, then hourly candles after the last full day."""
    d = daily[daily["end_ts"] <= t]
    last_daily_end = d["end_ts"].max() if len(d) else -np.inf
    h = hourly[(hourly["end_ts"] <= t) & (hourly["end_ts"] > last_daily_end)]
    return float(d["volume"].fillna(0).sum() + h["volume"].fillna(0).sum())


def price_at(t, hourly, daily):
    """Yes price at time t, with its source ('mid' or 'last') and the spread.

    Also returns the Yes bid and ask of that candle, needed to simulate execution.
    Uses the last candle ending at or before t. The midpoint is used when the book
    is two-sided and the spread is at most 10 cents; otherwise the last trade,
    if one happened in the previous 24 hours. Returns None when no price qualifies.
    """
    candles = hourly if len(hourly) and hourly["end_ts"].min() <= t else daily
    before = candles[candles["end_ts"] <= t]
    if before.empty:
        return None
    c = before.iloc[-1]
    two_sided = c["bid"] > 0 and c["ask"] < 1
    spread = c["ask"] - c["bid"] if two_sided else np.nan
    quotes = {"yes_bid": c["bid"], "yes_ask": c["ask"]}  # kept for execution in backtests
    if two_sided and spread <= MAX_SPREAD:
        return {"price": (c["bid"] + c["ask"]) / 2, "price_source": "mid", "spread": spread, **quotes}
    recent = before[(before["end_ts"] > t - FRESHNESS) & (before["volume"] > 0)]
    if len(recent) and 0 < recent.iloc[-1]["last"] < 1:
        return {"price": recent.iloc[-1]["last"], "price_source": "last", "spread": spread, **quotes}
    return None


def observations_for_market(m):
    """All horizon observations of one market (possibly none)."""
    hourly, daily = fetch_candles(m)
    obs = []
    for h in HORIZONS_BY_FAMILY[m["family"]]:
        t = m["close_ts"] - HORIZONS[h]
        if t < m["open_ts"]:
            continue  # market not open yet at this horizon
        p = price_at(t, hourly, daily)
        if p is None:
            continue
        obs.append({
            "ticker": m["ticker"], "event_ticker": m["event_ticker"],
            "series_ticker": m["series_ticker"], "family": m["family"],
            "horizon": h, "t": t, "close_ts": m["close_ts"],
            "outcome": int(m["result"] == "yes"),
            "volume_before": volume_before(t, hourly, daily),
            **p,
        })
    return obs


def collect_observations(markets, workers=6, report_every=1000):
    """Observations for many markets, fetched in parallel threads.

    The shared throttle in pmcal.kalshi keeps the overall request rate under
    the limit. Returns (observations DataFrame, list of (ticker, error)).
    """
    records = markets.to_dict("records")
    rows, failures, t0 = [], [], time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(observations_for_market, m): m["ticker"] for m in records}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                rows.extend(fut.result())
            except Exception as e:  # keep going; failures are reported to the caller
                failures.append((futures[fut], str(e)[:120]))
            if i % report_every == 0 or i == len(records):
                print(f"{i:,}/{len(records):,} markets, {len(rows):,} observations, {time.time() - t0:.0f}s", flush=True)
    return pd.DataFrame(rows), failures


def close_timing_check(markets):
    """Label check: in a fixed-date series, closing time must not depend on the outcome.

    Within each event holding both Yes and No markets, compute how many hours
    earlier the Yes market closed than the median No market. Comparing inside
    an event removes differences between games, days or releases. Returns the
    median of this gap per series; a large positive value reveals deadline
    behaviour (Yes resolves as soon as something happens).
    """
    m = markets[markets["result"].isin(["yes", "no"])]
    no_close = m[m["result"] == "no"].groupby("event_ticker")["close_ts"].median()
    yes = m[m["result"] == "yes"].join(no_close.rename("no_close_ts"), on="event_ticker", how="inner")
    yes["yes_earlier_h"] = (yes["no_close_ts"] - yes["close_ts"]) / 3600
    return (yes.groupby("series_ticker")["yes_earlier_h"]
               .agg(events="size", median_h="median", share_over_1h=lambda x: (x > 1).mean())
               .sort_values("median_h", ascending=False))
