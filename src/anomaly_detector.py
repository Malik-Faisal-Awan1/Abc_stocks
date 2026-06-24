# src/anomaly_detector.py

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_anomalies(ohlcv_df: pd.DataFrame) -> dict:
    """
    Train Isolation Forest on daily OHLCV features.
    Detects statistically unusual trading days.

    Args:
        ohlcv_df: Standard OHLCV DataFrame (date index, open/high/low/close/volume columns)

    Returns:
        dict with keys: anomaly_dates, anomaly_scores, feature_df,
                        anomaly_count, contamination_rate, model

    Raises:
        ValueError: If fewer than 10 rows after NaN drop.
    """
    if len(ohlcv_df) < 10:
        raise ValueError("Insufficient data for anomaly detection. Minimum 10 rows required.")

    features = pd.DataFrame(index=ohlcv_df.index)

    features["daily_return"] = ohlcv_df["close"].pct_change()
    features["volume_change"] = (
        (ohlcv_df["volume"] - ohlcv_df["volume"].rolling(5).mean())
        / ohlcv_df["volume"].rolling(5).mean()
    )
    features["price_range"] = (ohlcv_df["high"] - ohlcv_df["low"]) / ohlcv_df["close"]
    features["upper_shadow"] = (
        ohlcv_df["high"] - ohlcv_df[["open", "close"]].max(axis=1)
    ) / ohlcv_df["close"]
    features["lower_shadow"] = (
        ohlcv_df[["open", "close"]].min(axis=1) - ohlcv_df["low"]
    ) / ohlcv_df["close"]

    features = features.dropna()

    if len(features) < 10:
        raise ValueError("Insufficient data after dropping NaN rows.")

    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,   # ~5% of days expected to be anomalous
        random_state=42
    )
    model.fit(X)

    labels = model.predict(X)        # -1 = anomaly, 1 = normal
    scores = model.decision_function(X)  # More negative = more anomalous

    anomaly_mask = labels == -1
    anomaly_dates = features.index[anomaly_mask].tolist()
    anomaly_scores = pd.Series(scores, index=features.index)

    return {
        "anomaly_dates": anomaly_dates,
        "anomaly_scores": anomaly_scores,
        "feature_df": features,
        "anomaly_count": int(anomaly_mask.sum()),
        "contamination_rate": 0.05,
        "model": model,
    }
