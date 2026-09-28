# Are Prediction Markets Well Calibrated? Evidence from Kalshi

## Abstract

When a Kalshi contract trades at 70 cents, does the event happen 70% of the time? We study 12,970 price observations from 1,979 fixed-date Kalshi events, frozen at four horizons before resolution, and measure calibration with reliability diagrams, the Murphy decomposition of the Brier score, and a logistic calibration regression with event-clustered bootstrap intervals.

One day before resolution, prices are well calibrated: the calibration slope is 1.07 [0.98, 1.18], and 1.02 [0.92, 1.12] away from extreme prices. One hour before resolution, a favorite-longshot bias appears (slope 1.29 [1.21, 1.39]). It lives in the tails: part of it is a tick-size artifact, since 3,954 contracts quoted at 1 cent won only once, and it fades as prices move away from 0 and 1. A sports bias suggested by a smaller validation sample disappears in the full sample. Unexpectedly, the most liquid markets show a longshot bias one day out (slope 1.54 [1.19, 2.22]), the opposite of our liquidity hypothesis. None of the biases tested can be exploited by a trader who takes liquidity: the floor cent is available only to market makers, and backing sports favorites loses 2.38 cents per contract after the spread and fees.

## 1. Introduction

Prediction markets are often read as probability machines: a price of 70 cents is taken as a 70% chance. This reading is only valid if prices are **calibrated**, meaning that events priced at p happen with frequency p. Decades of research on betting markets document a **favorite-longshot bias**, where longshots are overpriced and favorites underpriced. Regulated event-contract exchanges such as Kalshi now offer a far larger and more varied sample of markets, from sports and elections to inflation prints and daily temperatures.

We ask four questions, fixed in a protocol before looking at the data:

| Hypothesis | Statement |
| --- | --- |
| H1: Horizon | Calibration improves as resolution approaches |
| H2: Favorite-longshot bias | Longshots are overpriced |
| H3: Cost of capital | The bias grows with time to resolution |
| H4: Liquidity and category | The bias is stronger in thin, retail-driven markets |

We then ask the question a trader cares about: can any bias found be exploited once the spread and fees are paid?

We exclude Polymarket due to French regulation.

## 2. Data

**Source.** All data comes from Kalshi's public API, which needs no key. Archived and recent markets are served by two tiers, and both are queried.

**Series selection.** Kalshi lists over 14,000 series, and volume is extremely concentrated: sports alone would dominate a volume-weighted sample. We keep the 25 largest series in each of six families (sports, politics, crypto, economics, weather, culture), or 150 series.

**Fixed-date markets only.** A market such as "X before December 31" closes as soon as X happens. Measuring its price a week before close would pick the moment just before the event for Yes outcomes, and a random moment for No outcomes: a look-ahead bias. We therefore keep only markets that resolve on a date known in advance. Each series is labelled from its contract design, never from outcome-dependent fields.

| Label | Definition | Series |
| --- | --- | --- |
| Fixed-date | Resolves on a date known when the market opens | 105 |
| Deadline | Can resolve as soon as something happens | 37 |
| Multi-stage | Fixed end date, but outcomes eliminated along the way | 8 |

The 105 fixed-date series carry 90% of the reviewed volume. Multi-stage series (tournament winners, primaries, reality shows) are excluded because a market closing at elimination would be kept or dropped depending on its outcome.

**Label check.** In a true fixed-date series, closing time does not depend on the outcome. Within each event, we measure how much earlier Yes markets close than No markets. Two of 97 series fail the check (the Spotify number-one song and Super Bowl guests) and are dropped. Both had been mislabelled by hand, which is exactly what the check is for.

**Filters and sample.** Of 423,937 settled markets, 184,383 remain after requiring a 0/1 settlement, at least 24 hours of trading and 1,000 contracts of lifetime volume. We draw 50 events per series, giving 22,229 markets in 3,423 events and 38,395 observations; 167 markets (0.75%) could not be retrieved after repeated API errors. The protocol keeps observations with at least 10,000 contracts traded before the horizon: 12,970 observations in 1,979 events.

## 3. Method

**Horizons.** Each market's price is frozen at T-1h, T-1d, T-7d and T-30d before its close. Sports markets close at the end of the game, so T-1h would measure in-play prices and is dropped. Weather markets open about 38 hours before closing, so only T-1h and T-1d exist.

**Price.** We use the midpoint of the bid and ask of the candlestick closest to the horizon when the spread is at most 10 cents, and otherwise the last trade if it is less than 24 hours old.

**Metrics.** The Brier score is the mean squared error between price and outcome. Its Murphy decomposition separates miscalibration (REL, lower is better) from discrimination (RES, higher is better) and the intrinsic difficulty of the sample (UNC):

```math
BS = \text{REL} - \text{RES} + \text{UNC}
```

The Brier Skill Score, BSS = 1 - BS / UNC, compares samples with different base rates. Our main test is the calibration regression:

```math
\text{logit}\,P(o_i = 1) = \alpha + \beta \cdot \text{logit}(p_i)
```

Perfect calibration gives α = 0 and β = 1. A slope β > 1 means prices sit too close to 50%: longshots are overpriced, the favorite-longshot bias.

**Inference.** Markets of the same event are correlated (the brackets of one temperature market, the two sides of one game). Confidence intervals therefore come from a bootstrap that resamples whole events.

**Validation.** Every tool was first run on simulated markets with a known truth. The slope is recovered (1.02 for a calibrated market, 1.27 for a true slope of 1.3), and the simulation revealed a trap: adding event shocks in logit space silently miscalibrates a market that looks calibrated. A Gaussian copula avoids it.

## 4. Results

### 4.1 Global calibration (H1)

| Horizon | Obs. | Events | β [95% CI] | BSS | REL | RES |
| --- | --- | --- | --- | --- | --- | --- |
| T-1h | 6,935 | 1,596 | 1.29 [1.21, 1.39] | 0.86 | 0.001 | 0.194 |
| T-1d | 3,803 | 978 | 1.07 [0.98, 1.18] | 0.62 | 0.000 | 0.143 |
| T-7d | 1,591 | 370 | 1.08 [0.97, 1.22] | 0.63 | 0.001 | 0.150 |
| T-30d | 641 | 156 | 1.07 [0.92, 1.30] | 0.64 | 0.004 | 0.147 |

From T-1d onwards, every slope is compatible with perfect calibration. As H1 predicts, discrimination is highest one hour before resolution. The one significant slope is at T-1h.

![Reliability diagrams by horizon](figures/reliability_by_horizon.png)

### 4.2 The near-resolution bias lives in the tails (H2)

Most Kalshi markets trade in whole cents, so the lowest Yes price is 1 cent. A market that is almost surely lost cannot trade below this floor, even if its true probability is 0.001. Of 3,954 observations at 1 cent or less, **only one won**.

The floor explains part of the T-1h slope, not all of it. The slope shrinks as the sample moves away from the extremes:

| T-1h prices kept | Obs. | β [95% CI] |
| --- | --- | --- |
| All | 6,935 | 1.29 [1.21, 1.39] |
| 0.02 to 0.98 | 2,135 | 1.19 [1.09, 1.30] |
| 0.05 to 0.95 | 1,475 | 1.13 [1.01, 1.29] |
| 0.10 to 0.90 | 1,061 | 1.05 [0.91, 1.21] |

The bias is concentrated in contracts priced a few cents from 0 or 1, where the 1-cent grid is coarse relative to the probabilities at stake. Between 10 and 90 cents, prices are calibrated even one hour out. Among families, the T-1h bias is clearest in economics (1.19 [1.08, 1.36], 1,642 obs.) and weather (1.35 [1.07, 2.01], 197 obs.).

**A lesson from the validation sample.** A first run with 10 events per series suggested a sports bias at T-1d (1.41 [1.03, 2.21], 70 events). With 368 events, the sports slope is 1.06 [0.88, 1.30]. The earlier result was noise, which is why the protocol required a larger sample before drawing conclusions.

![Calibration slope by family](figures/beta_by_family.png)

### 4.3 Cost of capital (H3)

A buyer of a favorite at price p ties up p dollars for T years. At a 4% rate, a rational buyer tolerates a mispricing of about p × r × T: for a 97-cent favorite, 0.3 percentage points at 30 days and 0.01 points at one day. Kalshi also pays interest on the value of open positions to eligible US users. As expected, the slope does not rise with the horizon (1.19, 1.02, 1.05, 1.02 from T-1h to T-30d, prices between 0.02 and 0.98). H3 is not supported.

### 4.4 Liquidity (H4)

| Contracts traded before T-1d | Obs. | Events | β [95% CI] |
| --- | --- | --- | --- |
| 10k to 50k | 1,443 | 654 | 0.97 [0.87, 1.09] |
| 50k to 500k | 759 | 365 | 1.05 [0.89, 1.25] |
| Over 500k | 153 | 96 | 1.54 [1.19, 2.22] |

Contrary to H4, the **most** liquid markets show a longshot bias one day out, while the others are calibrated. The effect is not driven by sports (it holds within economics, 1.42 [1.14, 1.98] across horizons) nor by horizon mix (heavy-volume observations are no more frequent near resolution). One candidate explanation is attention: the heaviest-traded markets are headline events (Fed decisions, CPI releases, prime-time games) that draw retail buyers of longshots. This subgroup analysis was not pre-registered and rests on 96 events, so it is exploratory.

### 4.5 Robustness

At T-1d, every variant gives a slope whose interval contains 1: volume thresholds of 1,000 (0.98) and 100,000 contracts (1.14), midpoint prices only (1.03), last-trade prices only (0.85), and each sub-period (1.06 for 2024 and earlier, 0.90 for 2025, 1.06 for 2026). At T-1h, the bias holds in most variants (1.17 with midpoints only, 1.22 in 2026) but not with volume above 100,000 contracts (1.11 [0.93, 1.38]) or in 2025 (1.03 [0.87, 1.30]).

## 5. Exploitability

Two strategies were fixed in advance and simulated with realistic execution: trades at the bid or ask, and Kalshi's taker fee, round_up(M × 0.07 × C × P × (1 - P)) to the next cent per order, with the multiplier M of each series and orders of 100 contracts.

**A. Selling lottery tickets at the floor.** Selling Yes at 1 cent means buying No at 99 cents. As a taker this needs a buyer of Yes resting at 1 cent, and only 1 of 3,954 floor observations had one: the 1-cent price is set by buyers lifting an offer already posted. The cent can only be collected as a **maker**. Assuming every posted offer is filled, the gain is 0.96 cents per contract at T-1h [0.89, 1.00], or about 1% of capital, with one loss in 2,876 trades. This is an upper bound: other makers already queue at that price and fills are not guaranteed. The tail risk is real: one loss costs 99 cents, as much as about a hundred wins.

**B. Backing sports favorites at T-1d.** Buying the favorite of every sports market, 711 trades in 358 events:

| Execution | P&L per contract, cents [95% CI] |
| --- | --- |
| Midpoint, no fee | -0.42 [-4.38, 3.47] |
| Ask, no fee | -1.10 [-5.03, 2.83] |
| Ask, taker fee | -2.38 [-6.30, 1.54] |

With the full sample there is no edge even before costs, consistent with sports being calibrated (section 4.2). The spread and fee then turn a zero edge into a loss of about 2.4 cents per contract.

**Not tested.** The longshot bias in the most liquid markets (section 4.4) was found after the strategies were fixed. Trading on it would require an out-of-sample test on new events first.

## 6. Limitations

- **Sample.** 50 events per series. Politics (26 events) and crypto (5 events) remain too small to analyse; most crypto volume sits in touch markets, which are excluded.
- **Subgroup results.** The liquidity finding is a subgroup analysis on 96 events and should be confirmed out of sample.
- **One platform.** Kalshi is a US-regulated exchange with its own fee schedule and tick sizes; results may not carry over to other markets.
- **Rule-based labels.** The fixed-date classification is partly manual. The label check caught two errors, but others may remain.
- **Execution.** Candlesticks give the top of the book, not its depth. Maker fills are assumed, not observed, so strategy A is an upper bound.
- **Missing data.** 167 markets (0.75%) could not be retrieved.

## 7. Conclusion

One day before resolution, Kalshi prices are well calibrated across families, horizons and every robustness variant tested. Near resolution, a favorite-longshot bias appears, but it is confined to contracts priced within a few cents of 0 or 1, where the 1-cent tick is coarse; between 10 and 90 cents, prices are calibrated even one hour out. A sports bias seen in a small sample vanished in the larger one, and backing sports favorites loses money after costs.

The one surprise runs against intuition: the most liquid markets, not the thinnest, show a longshot bias one day out. It deserves an out-of-sample test before anyone trades on it.

For a trader, the practical message is that edges on Kalshi are more likely to come from providing liquidity in the tails than from out-predicting the crowd.

## Appendix: reproducibility

Every number in this report is produced by the repository.

```bash
pip install -r requirements.txt
python tests/test_calibration.py
python scripts/collect_data.py --events-per-series 50
```

| Notebook | Content |
| --- | --- |
| 00_simulation_demo | Validation of the toolkit on simulated data |
| 01_series_universe | Series selection and fixed-date labels |
| 02_collected_data | Description of the sample |
| 03_global_calibration | Section 4.1 |
| 04_bias_analysis | Sections 4.2 to 4.5 |
| 05_exploitability | Section 5 |

The research protocol, with hypotheses, horizons, filters and robustness checks, was written before the data was examined.
