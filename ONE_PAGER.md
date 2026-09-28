# Are prediction markets well calibrated? Evidence from Kalshi

**Question.** When a Kalshi contract trades at 70 cents, does the event happen 70% of the time? And if not, can a trader profit once the spread and fees are paid?

**Data.** Public Kalshi API. 105 fixed-date series across sports, economics, weather, culture, politics and crypto, selected from 150 reviewed; 184,383 filtered markets; 12,970 price observations in 1,979 events, frozen 1 hour, 1 day, 7 days and 30 days before close. Deadline markets ("X before December 31") are excluded to avoid look-ahead bias, and a data check confirms that closing times do not depend on outcomes.

**Method.** Reliability diagrams, Brier score with its Murphy decomposition, and the calibration regression logit P(o = 1) = a + b logit(p), with confidence intervals from a bootstrap that resamples whole events. Hypotheses and robustness checks were fixed in a protocol before looking at the data, and every tool was validated on simulated markets with a known truth.

**Findings.**

1. One day before resolution, prices are well calibrated: slope 1.07 [0.98, 1.18], robust to volume thresholds, price definitions and sub-periods.
2. One hour before resolution, a favorite-longshot bias appears (1.29 [1.21, 1.39]), confined to the tails. Contracts at the 1-cent floor won once in 3,954 cases; between 10 and 90 cents the slope is 1.05 [0.91, 1.21].
3. A sports bias found in a first sample of 70 events disappeared with 368 events: a small-sample false positive caught by the protocol.
4. Surprise: the most liquid markets show a longshot bias one day out (1.54 [1.19, 2.22], 96 events), the opposite of the usual liquidity story. Exploratory.
5. The cost of capital cannot explain any bias at these horizons (at most 0.3 percentage points at 30 days).

**Can it be traded?**

- Selling lottery tickets at 1 cent: impossible as a taker (1 of 3,954 floor quotes had a buyer); up to about 1 cent per contract as a maker, an upper bound since other makers already queue there.
- Backing sports favorites: -0.42 cents per contract at the midpoint, -2.38 after the spread and taker fees.

**Takeaway.** Kalshi is well calibrated away from the extremes. The visible biases sit in the tails near resolution, where the tick size binds, and the rent there goes to liquidity providers. The liquidity surprise is the one lead worth an out-of-sample test.

**Stack.** Python (numpy, pandas, scipy, matplotlib), Jupyter, a resumable data pipeline with caching and rate limiting, unit tests.
