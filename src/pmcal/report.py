"""Helpers shared by the analysis notebooks: statistics with cluster-bootstrap CIs."""
import numpy as np
import pandas as pd

from pmcal.calibration import calibration_regression, cluster_bootstrap, murphy, reliability_table

HORIZON_ORDER = ["1h", "1d", "7d", "30d"]


def stats(d, n_bins=10, strategy="uniform"):
    alpha, beta = calibration_regression(d["price"], d["outcome"])
    m = murphy(d["price"], d["outcome"], n_bins, strategy)
    return {"alpha": alpha, "beta": beta, "BS": m["BS"], "REL": m["REL"], "RES": m["RES"],
            "UNC": m["UNC"], "BSS": m["BSS"]}


def with_ci(d, n_boot, stat_fn=stats, **labels):
    """One row: labels, sample sizes, each statistic with its 95% cluster-bootstrap CI."""
    ci = cluster_bootstrap(d, stat_fn, "event_ticker", n_boot=n_boot)
    row = {**labels, "n_obs": len(d), "n_events": d["event_ticker"].nunique()}
    for s in ci.index:
        row[s] = ci.loc[s, "estimate"]
        row[s + "_lo"], row[s + "_hi"] = ci.loc[s, "ci_low"], ci.loc[s, "ci_high"]
    return row


def fmt(v, lo, hi, d=2):
    if np.isnan(v):
        return "not identified"
    return f"{v:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def fold(d):
    """Favorite view: price of the more likely side and whether the favorite won."""
    out = d.copy()
    yes_fav = out["price"] >= 0.5
    out["price"] = np.where(yes_fav, out["price"], 1 - out["price"])
    out["outcome"] = np.where(yes_fav, out["outcome"], 1 - out["outcome"])
    return out
