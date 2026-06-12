"""
Tests for src/anomaly_detector.py
Phase 3 — 5 required tests per PRD §11
"""
import pytest
import numpy as np
import pandas as pd
from src.anomaly_detector import detect_anomalies


# ---------------------------------------------------------------------------
# Test fixture — 90-day mock OHLCV DataFrame
# ---------------------------------------------------------------------------
def make_mock_ohlcv(n: int = 90, seed: int = 42) -> pd.DataFrame:
    """Generate a reproducible mock OHLCV DataFrame with n rows."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = 150.0 + rng.normal(0, 2, n).cumsum()
    open_ = close + rng.normal(0, 0.5, n)
    high = np.maximum(close, open_) + rng.uniform(0.1, 1.5, n)
    low = np.minimum(close, open_) - rng.uniform(0.1, 1.5, n)
    volume = rng.integers(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


# ---------------------------------------------------------------------------
# Test 1 — Output dict has all required keys
# ---------------------------------------------------------------------------
def test_detect_returns_required_keys():
    df = make_mock_ohlcv()
    result = detect_anomalies(df)
    required_keys = {"anomaly_dates", "anomaly_scores", "feature_df",
                     "anomaly_count", "contamination_rate", "model"}
    assert required_keys.issubset(result.keys()), (
        f"Missing keys: {required_keys - result.keys()}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Anomaly count is reasonable for a 90-day window
# ---------------------------------------------------------------------------
def test_anomaly_count_is_reasonable():
    df = make_mock_ohlcv()
    result = detect_anomalies(df)
    assert 1 <= result["anomaly_count"] <= 10, (
        f"Expected 1–10 anomalies, got {result['anomaly_count']}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Fewer than 10 rows raises ValueError
# ---------------------------------------------------------------------------
def test_insufficient_data_raises():
    df = make_mock_ohlcv(n=5)
    with pytest.raises(ValueError):
        detect_anomalies(df)


# ---------------------------------------------------------------------------
# Test 4 — All anomaly_dates exist in ohlcv_df.index
# ---------------------------------------------------------------------------
def test_anomaly_dates_are_in_index():
    df = make_mock_ohlcv()
    result = detect_anomalies(df)
    for date in result["anomaly_dates"]:
        assert date in df.index, f"Anomaly date {date} not found in OHLCV index"


# ---------------------------------------------------------------------------
# Test 5 — contamination_rate is exactly 0.05
# ---------------------------------------------------------------------------
def test_contamination_rate_is_correct():
    df = make_mock_ohlcv()
    result = detect_anomalies(df)
    assert result["contamination_rate"] == 0.05, (
        f"Expected contamination_rate=0.05, got {result['contamination_rate']}"
    )
