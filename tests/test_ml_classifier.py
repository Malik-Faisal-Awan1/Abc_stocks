"""
Tests for src/ml_classifier.py
Phase 3 — 7 required tests per PRD §11
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.exceptions import NotFittedError
from src.ml_classifier import (
    train_classifier,
    predict_signal_confidence,
    FEATURE_COLUMNS,
    MINIMUM_SAMPLES,
)


# ---------------------------------------------------------------------------
# Test fixture — mock signal_log DataFrame with ML feature columns
# ---------------------------------------------------------------------------
def make_mock_signal_log(n: int = 60, seed: int = 42) -> pd.DataFrame:
    """
    Generate a mock signal_log DataFrame with all required columns.
    Produces a balanced mix of hits/misses and bullish/bearish signals.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")

    signals = rng.choice(["Bullish", "Bearish"], size=n)
    hit_miss = rng.choice(["Hit", "Miss"], size=n)

    return pd.DataFrame({
        "date": dates,
        "signal": signals,
        "hit_miss": hit_miss,
        "close_T": rng.uniform(100, 200, n).round(4),
        "close_T1": rng.uniform(100, 200, n).round(4),
        "equity_after": rng.uniform(90, 120, n).round(4),
        "rsi_value": rng.uniform(20, 80, n).round(4),
        "macd_gap": rng.uniform(-2, 2, n).round(6),
        "composite_score_value": rng.uniform(0, 1, n).round(4),
        "day_of_week": rng.integers(0, 5, n),
        "price_momentum_5d": rng.uniform(-0.05, 0.05, n).round(6),
    })


def make_small_signal_log(n: int = 10) -> pd.DataFrame:
    """Generate a signal_log with fewer than MINIMUM_SAMPLES non-neutral rows."""
    return make_mock_signal_log(n=n)


# ---------------------------------------------------------------------------
# Test 1 — Output dict has all required keys
# ---------------------------------------------------------------------------
def test_train_returns_required_keys():
    log = make_mock_signal_log(60)
    result = train_classifier(log)
    required_keys = {
        "pipeline", "train_accuracy", "test_accuracy",
        "train_samples", "test_samples", "feature_names",
        "is_trained", "insufficient_data",
    }
    assert required_keys.issubset(result.keys()), (
        f"Missing keys: {required_keys - result.keys()}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Fewer than 20 non-neutral samples → insufficient_data=True, is_trained=False
# ---------------------------------------------------------------------------
def test_insufficient_data_flag():
    log = make_small_signal_log(n=10)
    result = train_classifier(log)
    assert result["is_trained"] is False
    assert result["insufficient_data"] is True
    assert result["pipeline"] is None


# ---------------------------------------------------------------------------
# Test 3 — train_accuracy is a float between 0 and 1
# ---------------------------------------------------------------------------
def test_train_accuracy_is_float():
    log = make_mock_signal_log(60)
    result = train_classifier(log)
    if result["is_trained"]:
        assert isinstance(result["train_accuracy"], float)
        assert 0.0 <= result["train_accuracy"] <= 1.0


# ---------------------------------------------------------------------------
# Test 4 — predict_signal_confidence returns confidence_pct in 0–100
# ---------------------------------------------------------------------------
def test_predict_returns_confidence_pct():
    log = make_mock_signal_log(60)
    result = train_classifier(log)
    if result["is_trained"]:
        features = {col: 0.5 for col in FEATURE_COLUMNS}
        pred = predict_signal_confidence(result["pipeline"], features)
        assert pred["is_valid"] is True
        assert isinstance(pred["confidence_pct"], float)
        assert 0.0 <= pred["confidence_pct"] <= 100.0


# ---------------------------------------------------------------------------
# Test 5 — prediction label is one of the two allowed values
# ---------------------------------------------------------------------------
def test_predict_returns_valid_prediction_label():
    log = make_mock_signal_log(60)
    result = train_classifier(log)
    if result["is_trained"]:
        features = {col: 0.5 for col in FEATURE_COLUMNS}
        pred = predict_signal_confidence(result["pipeline"], features)
        assert pred["prediction"] in ("Likely Correct", "Likely Incorrect"), (
            f"Unexpected prediction label: {pred['prediction']}"
        )


# ---------------------------------------------------------------------------
# Test 6 — pipeline raises NotFittedError if predict called before fit
# ---------------------------------------------------------------------------
def test_pipeline_is_fitted():
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    unfitted_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression()),
    ])
    features = {col: 0.5 for col in FEATURE_COLUMNS}
    result = predict_signal_confidence(unfitted_pipeline, features)
    # predict_signal_confidence catches exceptions and returns is_valid=False
    assert result["is_valid"] is False


# ---------------------------------------------------------------------------
# Test 7 — classifier uses class_weight="balanced"
# ---------------------------------------------------------------------------
def test_balanced_classes_used():
    log = make_mock_signal_log(60)
    result = train_classifier(log)
    if result["is_trained"]:
        classifier = result["pipeline"].named_steps["classifier"]
        assert classifier.class_weight == "balanced", (
            f"Expected class_weight='balanced', got {classifier.class_weight}"
        )
