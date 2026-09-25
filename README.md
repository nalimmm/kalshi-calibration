# Are prediction markets well calibrated? Evidence from Kalshi

When a Kalshi contract trades at 70 cents, does the event happen 70% of the time?
This project measures where, when and why Kalshi prices deviate from realized
frequencies, and whether those deviations survive fees and the cost of capital.

We exclude Polymarket due to French regulation.

## Key findings (provisional, validation sample)

- **Calibrated one day out.** At T-1d the calibration slope is 1.05 [0.89, 1.29]: prices match realized frequencies, and every robustness variant agrees.
- **The near-resolution bias is a tick-size artifact.** At T-1h, 915 contracts quoted at 1 cent never won: prices cannot fall below the 1-cent floor. Without extreme prices, the bias is no longer significant.
- **Sports is the exception, and fees eat it.** Sports favorites are underpriced (slope 1.48 [1.07, 2.21]), but backing them earns +1.75 cents per contract at the midpoint and -0.13 cents after the spread and taker fees.
- **The floor rent goes to makers.** Almost no floor quote has a Yes bid, so a taker cannot collect the cent; only a market maker posting offers at 1 cent can.

Full write-up: `ONE_PAGER.md` for the summary, the report for the details.

## Research question

1. **Horizon**: does calibration improve as resolution approaches?
2. **Favorite-longshot bias**: are longshots overpriced?
3. **Cost of capital**: does the bias grow with time to resolution?
4. **Liquidity and category**: is the bias stronger in thin, retail-driven markets?

The full protocol (scope, horizons, filters, metrics, robustness checks) was
fixed before looking at the data.

## Method in one paragraph

Only **fixed-date markets** are studied (games, data releases, elections,
daily weather), because markets that can resolve early ("X before December 31")
create look-ahead bias. Each market's price is frozen at fixed horizons before
resolution and compared with its 0/1 outcome, using reliability diagrams, the
Brier score with its Murphy decomposition, and a logistic calibration regression.
Confidence intervals come from a bootstrap that resamples whole events, since
markets of the same event are correlated.

## Repository structure

```
scripts/
    collect_data.py         collects markets and prices at each horizon (resumable)
src/pmcal/
    calibration.py          calibration metrics and cluster bootstrap
    collect.py              market filters, label check, price extraction
    kalshi.py               read-only client for the public Kalshi API, with disk cache
    report.py               shared helpers: statistics with cluster-bootstrap CIs
notebooks/
    00_simulation_demo      validates the toolkit on simulated data with a known truth
    01_series_universe      selects the series and labels them fixed-date / deadline / multi-stage
    02_collected_data       describes the collected sample
    03_global_calibration   reliability, Murphy decomposition, calibration slope by horizon and family
    04_bias_analysis        favorite-longshot bias, tick-size artifact, cost of capital, liquidity, robustness
    05_exploitability       two pre-specified strategies with realistic execution and Kalshi fees
data/
    series_universe.csv     the labelled series, part of the protocol
    observations.parquet    one row per market and horizon (output of the script)
figures/
tests/
```

## Status

- [x] Research protocol
- [x] Calibration toolkit, validated on simulated data
- [x] Series universe and fixed-date classification
- [x] Market and price collection at each horizon
- [x] Global calibration (provisional: validation sample of 10 events per series)
- [x] Bias analysis by horizon, liquidity and category (provisional)
- [x] Exploitability test net of fees (provisional)
- [ ] Write-up

## How to run

```bash
pip install -r requirements.txt
python tests/test_calibration.py

# collect the data (resumable: rerun the same command if interrupted)
python scripts/collect_data.py --events-per-series 50   # about 2 hours
python scripts/collect_data.py --all                    # full study, about 13 to 14 hours

jupyter notebook notebooks/
```

No API key is needed: Kalshi market data is public. API responses are cached in
`data/raw/cache/`, which is not committed.
