"""Calibration tools for prediction markets.

Conventions:
    p: price of the Yes contract, in (0, 1) (implied probability)
    o: outcome, 1 if the event happened, 0 otherwise
    clusters: event identifier (Kalshi event_ticker), used for the bootstrap
"""
import numpy as np
import pandas as pd

EPS = 1e-4  # avoids logit(0) and logit(1)


def logit(x):
    x = np.clip(x, EPS, 1 - EPS)
    return np.log(x / (1 - x))


def make_bins(p, n_bins=10, strategy="uniform"):
    """Return the bin index of each price.

    uniform:  bins of equal width on [0, 1]
    quantile: bins holding (roughly) the same number of observations
    """
    if strategy == "uniform":
        edges = np.linspace(0, 1, n_bins + 1)
    elif strategy == "quantile":
        edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
        edges[0], edges[-1] = 0.0, 1.0
    else:
        raise ValueError("strategy must be 'uniform' or 'quantile'")
    # digitize on the inner edges -> indices 0..n_bins-1
    return np.digitize(p, edges[1:-1], right=False)


def reliability_table(p, o, n_bins=10, strategy="uniform"):
    """One row per bin: count, mean price, observed frequency."""
    df = pd.DataFrame({"p": p, "o": o, "bin": make_bins(p, n_bins, strategy)})
    tab = df.groupby("bin").agg(n=("o", "size"), p_mean=("p", "mean"), o_mean=("o", "mean"))
    return tab.reset_index()


def brier(p, o):
    return float(np.mean((np.asarray(p) - np.asarray(o)) ** 2))


def murphy(p, o, n_bins=10, strategy="uniform"):
    """Murphy decomposition: BS = REL - RES + UNC (approximately).

    Exact when prices take a single value per bin. With continuous prices,
    the gap is reported in 'residual' (within-bin variance).
    """
    p, o = np.asarray(p, float), np.asarray(o, float)
    tab = reliability_table(p, o, n_bins, strategy)
    n, o_bar = len(o), o.mean()
    rel = np.sum(tab.n * (tab.p_mean - tab.o_mean) ** 2) / n
    res = np.sum(tab.n * (tab.o_mean - o_bar) ** 2) / n
    unc = o_bar * (1 - o_bar)
    bs = brier(p, o)
    return {
        "BS": bs, "REL": rel, "RES": res, "UNC": unc,
        "residual": bs - (rel - res + unc),
        "BSS": 1 - bs / unc if unc > 0 else np.nan,
    }


def calibration_regression(p, o, n_iter=50, tol=1e-10):
    """Logistic regression of o on logit(p), fitted by Newton-Raphson.

    Returns (alpha, beta). Perfect calibration: alpha = 0, beta = 1.
    beta > 1: prices too close to 50% (favorite-longshot bias).
    beta < 1: prices too extreme (overconfident market).

    Returns (nan, nan) when the slope is not identified: a single outcome value,
    or a sample where prices separate outcomes perfectly (common in small bootstrap draws).
    """
    x = logit(np.asarray(p, float))
    y = np.asarray(o, float)
    if y.min() == y.max():
        return np.nan, np.nan
    X = np.column_stack([np.ones_like(x), x])
    w = np.array([0.0, 1.0])  # start from perfect calibration
    for _ in range(n_iter):
        mu = 1 / (1 + np.exp(-np.clip(X @ w, -500, 500)))  # clip: no overflow when a draw nearly separates
        grad = X.T @ (y - mu)
        hess = X.T @ (X * (mu * (1 - mu))[:, None])
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return np.nan, np.nan
        w += step
        if np.max(np.abs(step)) < tol:
            return float(w[0]), float(w[1])
    return np.nan, np.nan  # no convergence: perfect separation


def cluster_bootstrap(df, stat_fn, cluster_col="cluster", n_boot=2000, seed=0):
    """95% confidence interval from resampling whole clusters with replacement.

    df:      DataFrame with the columns used by stat_fn and cluster_col
    stat_fn: function DataFrame -> dict of statistics
    Returns a DataFrame: estimate, 2.5% lower bound, 97.5% upper bound.
    """
    rng = np.random.default_rng(seed)
    codes, _ = pd.factorize(df[cluster_col])
    order = np.argsort(codes, kind="stable")      # rows sorted by cluster
    sizes = np.bincount(codes)
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    n_clusters = len(sizes)
    draws = []
    for _ in range(n_boot):
        picked = rng.integers(0, n_clusters, n_clusters)
        lengths = sizes[picked]
        # positions of every row of every picked cluster, without a Python loop over clusters
        within = np.arange(lengths.sum()) - np.repeat(np.cumsum(lengths) - lengths, lengths)
        rows = order[np.repeat(starts[picked], lengths) + within]
        draws.append(stat_fn(df.iloc[rows]))
    draws = pd.DataFrame(draws)
    point = pd.Series(stat_fn(df))
    return pd.DataFrame({
        "estimate": point,
        "ci_low": draws.quantile(0.025),
        "ci_high": draws.quantile(0.975),
    })


def plot_reliability(ax, p, o, n_bins=10, strategy="uniform", label=None):
    """Reliability diagram: observed frequency against mean price, by bin.

    Error bars are simple binomial bands (+/- 1.96 standard errors): they are
    indicative only and ignore within-cluster correlation.
    """
    tab = reliability_table(p, o, n_bins, strategy)
    se = np.sqrt(tab.o_mean * (1 - tab.o_mean) / tab.n)
    ax.errorbar(tab.p_mean, tab.o_mean, yerr=1.96 * se, fmt="o-", capsize=3, label=label)
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
    ax.set_xlabel("Mean bin price (implied probability)")
    ax.set_ylabel("Observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    return tab
