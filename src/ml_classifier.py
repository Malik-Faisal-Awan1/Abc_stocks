# src/ml_classifier.py
"""
ML Signal Classifier module.
Trains a Logistic Regression pipeline on backtesting signal_log to predict
whether the current signal is likely correct.
No Streamlit imports. No data fetching. Data received from app layer.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "rsi_value",
    "macd_gap",
    "composite_score_value",
    "day_of_week",
    "price_momentum_5d",
]

MINIMUM_SAMPLES = 20


def train_classifier(signal_log: pd.DataFrame) -> dict:
    """
    Train logistic regression classifier on backtesting signal outcomes.

    Args:
        signal_log: DataFrame from run_backtest() including feature columns
                    added in Phase 3.

    Returns:
        dict with keys: pipeline, train_accuracy, test_accuracy,
                        train_samples, test_samples, feature_names,
                        is_trained, insufficient_data
    """
    # Validate required columns exist
    required_cols = FEATURE_COLUMNS + ["hit_miss", "signal"]
    missing = [c for c in required_cols if c not in signal_log.columns]
    if missing:
        raise ValueError(f"signal_log missing required columns: {missing}")

    # Filter to non-neutral signals only
    valid = signal_log[signal_log["signal"] != "Neutral"].copy()
    valid["label"] = (valid["hit_miss"] == "Hit").astype(int)

    # Hard gate — minimum samples
    if len(valid) < MINIMUM_SAMPLES:
        return {
            "pipeline": None,
            "train_accuracy": None,
            "test_accuracy": None,
            "train_samples": len(valid),
            "test_samples": 0,
            "feature_names": FEATURE_COLUMNS,
            "is_trained": False,
            "insufficient_data": True,
        }

    X = valid[FEATURE_COLUMNS].values
    y = valid["label"].values

    # 80/20 train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Pipeline: scale + classify
    # Fixed hyperparameters — not tunable
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            class_weight="balanced"
        ))
    ])
    pipeline.fit(X_train, y_train)

    train_acc = round(float(pipeline.score(X_train, y_train)), 4)
    test_acc = round(float(pipeline.score(X_test, y_test)), 4)

    return {
        "pipeline": pipeline,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_names": FEATURE_COLUMNS,
        "is_trained": True,
        "insufficient_data": False,
    }


def predict_signal_confidence(pipeline, current_features: dict) -> dict:
    """
    Predict probability the current signal is correct.

    Args:
        pipeline: Fitted Pipeline from train_classifier()
        current_features: Dict with FEATURE_COLUMNS as keys

    Returns:
        dict with keys: confidence_pct, prediction, is_valid
    """
    try:
        X = [[current_features[f] for f in FEATURE_COLUMNS]]
        proba = pipeline.predict_proba(X)[0]
        confidence = round(float(proba[1]) * 100, 1)  # P(Hit)
        prediction = "Likely Correct" if confidence >= 50 else "Likely Incorrect"
        return {
            "confidence_pct": confidence,
            "prediction": prediction,
            "is_valid": True,
        }
    except Exception:
        return {"confidence_pct": None, "prediction": None, "is_valid": False}


def save_model(pipeline, ticker: str) -> None:
    """Persist trained pipeline to models/<TICKER>_classifier.pkl."""
    path = Path("models") / f"{ticker.upper()}_classifier.pkl"
    path.parent.mkdir(exist_ok=True)
    joblib.dump(pipeline, path)


def load_model(ticker: str):
    """Load a previously saved pipeline, or return None if not found."""
    path = Path("models") / f"{ticker.upper()}_classifier.pkl"
    if not path.exists():
        return None
    return joblib.load(path)
