# Are prediction markets well calibrated? Evidence from Kalshi

**Question.** When a Kalshi contract trades at 70 cents, does the event happen 70% of the time? And if not, can a trader profit once the spread and fees are paid?

**Data.** Public Kalshi API. 105 fixed-date series across sports, economics, weather, culture, politics and crypto, selected from 150 reviewed; 421,502 settled markets; validation sample of 4,438 price observations in 460 events, frozen 1 hour, 1 day, 7 days and 30 days before close. Deadline markets ("X before December 31") are excluded to avoid look-ahead bias, and a data check confirms that closing times do not depend on outcomes.

**Method.** Reliability diagrams, Brier score with its Murphy decomposition, and the calibration regression logit P(o = 1) = a + b logit(p), with confidence intervals from a bootstrap that resamples whole events. Hypotheses and robustness checks were fixed in a protocol before looking at the data, and every tool was validated on simulated markets with a known truth.

**Findings.**

1. One day before resolution, prices are well calibrated: slope 1.05 [0.89, 1.29], robust to volume thresholds, price definitions, binning and sub-periods.
2. The apparent favorite-longshot bias one hour before resolution is a tick-size artifact. Prices cannot go below 1 cent, and the 915 contracts quoted there never won. Excluding extreme prices removes the significance.
3. Sports show a genuine favorite-longshot bias (slope 1.48 [1.07, 2.21]), in line with the betting literature.
4. The cost of capital cannot explain any bias at these horizons (at most 0.3 percentage points at 30 days), and Kalshi pays interest on open positions to eligible US users.

**Can it be traded?**

- Backing sports favorites: +1.75 cents per contract at the midpoint, +1.14 at the ask, -0.13 after taker fees. The fee absorbs the bias.
- Selling lottery tickets at 1 cent: impossible as a taker (1 of 1,436 floor quotes had a buyer); up to 1 cent per contract as a maker, an upper bound since other makers already queue there.

**Takeaway.** Kalshi is efficient up to transaction costs. The visible biases are either microstructure rents collected by liquidity providers or smaller than the fee. Edges are more likely to come from providing liquidity than from out-predicting the crowd.

**Stack.** Python (numpy, pandas, scipy, matplotlib), Jupyter, a resumable data pipeline with caching and rate limiting, unit tests.

*Provisional: validation sample of 10 events per series; the full run will update every number.*
