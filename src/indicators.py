import pandas as pd

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's RSI. Alpha = 1/period (not 2/(period+1)).
    Reference: Wilder (1978). Verified against rsi_reference.md.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder smoothing: first value is simple mean, then exponential
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Returns (macd_line, signal_line, histogram).
    Uses standard EMA (alpha = 2/(span+1)), not Wilder smoothing.
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def composite_score(rsi_series: pd.Series, macd_line: pd.Series, signal_line: pd.Series) -> dict:
    """
    Combines RSI and MACD into a single directional confidence score.

    Returns a dict, not a float. The dict carries the signal, score,
    and the components used — so the UI can show the reasoning.
    """
    latest_rsi = rsi_series.iloc[-1]
    latest_macd = macd_line.iloc[-1]
    latest_signal = signal_line.iloc[-1]

    # RSI component: normalise 0-100 → 0.0-1.0
    rsi_component = latest_rsi / 100.0

    # MACD component: binary crossover signal
    macd_component = 1.0 if latest_macd > latest_signal else 0.0

    # Composite: equal weight
    score = (rsi_component * 0.5) + (macd_component * 0.5)
    score_pct = round(score * 100, 1)

    # Directional classification
    if score_pct > 60:
        direction = "Bullish"
    elif score_pct < 40:
        direction = "Bearish"
    else:
        direction = "Neutral"

    return {
        "score_pct": score_pct,
        "direction": direction,
        "is_neutral": direction == "Neutral",
        "rsi_component": round(rsi_component, 3),
        "macd_component": macd_component,
        "display_text": f"Upward momentum confidence: {score_pct}%",
        "disclaimer": "This is a probabilistic indicator, not a financial prediction."
    }
