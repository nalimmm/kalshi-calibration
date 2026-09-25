"""Tests: run with `python test_calibration.py`."""
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pmcal.calibration import murphy, calibration_regression, logit


def test_worked_example():
    # 5 markets at 80% (3 Yes), 5 markets at 20% (1 Yes)
    p = np.array([0.8] * 5 + [0.2] * 5)
    o = np.array([1, 1, 1, 0, 0] + [1, 0, 0, 0, 0])
    m = murphy(p, o)
    assert np.isclose(m["BS"], 0.22)
    assert np.isclose(m["REL"], 0.02)
    assert np.isclose(m["RES"], 0.04)
    assert np.isclose(m["UNC"], 0.24)
    assert np.isclose(m["residual"], 0.0)


def test_murphy_identity_discrete_prices():
    rng = np.random.default_rng(1)
    p = rng.choice([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], 5000)
    o = rng.random(5000) < p
    m = murphy(p, o)
    assert abs(m["residual"]) < 1e-12


def test_regression_recovers_beta():
    rng = np.random.default_rng(2)
    n = 200_000
    p = rng.uniform(0.02, 0.98, n)
    for true_beta in [1.0, 1.3, 0.8]:
        q = 1 / (1 + np.exp(-true_beta * logit(p)))  # true probability
        o = rng.random(n) < q
        a, b = calibration_regression(p, o)
        assert abs(b - true_beta) < 0.03, (true_beta, b)
        assert abs(a) < 0.03


if __name__ == "__main__":
    test_worked_example()
    test_murphy_identity_discrete_prices()
    test_regression_recovers_beta()
    print("All tests pass.")
