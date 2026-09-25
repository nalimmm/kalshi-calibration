"""Collect Kalshi data for the calibration study.

Usage (from the repository root):
    python scripts/collect_data.py --events-per-series 50
    python scripts/collect_data.py --all          # full study, about 13 to 14 hours

What it does:
    1. Lists the settled markets of every fixed-date series in data/series_universe.csv.
    2. Applies the market-level filters of the protocol.
    3. Runs the close-timing label check and drops series that behave like deadline markets.
    4. Samples events (nested: 15 events per series is a subset of 50, which is a subset of all).
    5. Extracts prices and prior volume at each horizon.

Outputs, in data/:
    markets.parquet        filtered markets, before sampling
    label_check.csv        close-timing check per series
    observations.parquet   one row per market and horizon

Every API response is cached in data/raw/cache/. If the script is interrupted,
run the same command again: finished requests are read from the cache.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pmcal import collect  # noqa: E402

DATA = ROOT / "data"
MIN_LIFETIME_VOLUME = 1_000   # lowest sensitivity threshold of the protocol
DEADLINE_GAP_HOURS = 1        # label check: Yes closing more than 1h earlier than No


def list_markets(universe):
    frames = []
    fixed = universe[universe["label"] == "fixed-date"].to_dict("records")
    for i, row in enumerate(fixed, 1):
        frames.append(collect.markets_table(row))
        print(f"  [{i}/{len(fixed)}] {row['ticker']}: {len(frames[-1]):,} markets", flush=True)
    return pd.concat(frames, ignore_index=True)


def apply_filters(markets):
    steps = {"all settled": len(markets)}
    m = markets[markets["result"].isin(["yes", "no"])]
    steps["settled at 0 or 1"] = len(m)
    m = m[m["close_ts"] - m["open_ts"] >= collect.DAY]
    steps["open at least 24h"] = len(m)
    m = m[m["lifetime_volume"] >= MIN_LIFETIME_VOLUME]
    steps["lifetime volume >= 1,000"] = len(m)
    for name, n in steps.items():
        print(f"  {name:<28} {n:>10,}")
    return m


def sample_events(markets, events_per_series):
    """Nested sample: each series gets a fixed random order of its events, seeded by its name."""
    if events_per_series is None:
        return markets
    keep = []
    for series, g in markets.groupby("series_ticker"):
        seed = int(hashlib.sha1(series.encode()).hexdigest()[:8], 16)
        events = np.sort(g["event_ticker"].unique())
        keep.extend(np.random.default_rng(seed).permutation(events)[:events_per_series])
    return markets[markets["event_ticker"].isin(keep)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    size = parser.add_mutually_exclusive_group(required=True)
    size.add_argument("--events-per-series", type=int, help="number of events sampled in each series")
    size.add_argument("--all", action="store_true", help="use every event (full study)")
    parser.add_argument("--workers", type=int, default=30, help="parallel requests in flight (default 30)")
    args = parser.parse_args()
    t0 = time.time()

    print("1. Listing settled markets")
    universe = pd.read_csv(DATA / "series_universe.csv")
    markets = list_markets(universe)

    print("2. Market-level filters")
    markets = apply_filters(markets)
    markets.to_parquet(DATA / "markets.parquet", index=False)

    print("3. Label check")
    timing = collect.close_timing_check(markets)
    timing.to_csv(DATA / "label_check.csv")
    flagged = timing.index[timing["median_h"] > DEADLINE_GAP_HOURS]
    print(f"  {len(flagged)} series behave like deadline markets and are dropped: {', '.join(flagged) or 'none'}")
    markets = markets[~markets["series_ticker"].isin(flagged)]

    print("4. Sampling events")
    sample = sample_events(markets, None if args.all else args.events_per_series)
    n_calls = len(sample) + int((sample["close_ts"] - sample["open_ts"] > collect.HOURLY_WINDOW).sum())
    print(f"  {len(sample):,} markets in {sample['event_ticker'].nunique():,} events, "
          f"about {n_calls:,} API calls (roughly {n_calls / 4 / 3600:.1f} hours if nothing is cached)")

    print("5. Prices at each horizon")
    obs, failures = collect.collect_observations(sample, workers=args.workers)
    obs.to_parquet(DATA / "observations.parquet", index=False)
    print(f"  {len(obs):,} observations saved, {len(failures)} markets failed")
    (DATA / "failures.csv").unlink(missing_ok=True)
    if failures:
        pd.DataFrame(failures, columns=["ticker", "error"]).to_csv(DATA / "failures.csv", index=False)
        print("  failed markets listed in data/failures.csv: rerun the script to retry them")
    print(f"Done in {(time.time() - t0) / 60:.0f} minutes")


if __name__ == "__main__":
    main()
