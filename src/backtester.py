from src.indicators import calculate_rsi, calculate_macd, composite_score
from decimal import Decimal
import pandas as pd

def run_backtest(ohlcv_df: pd.DataFrame, ticker: str) -> dict:
    
    initial_len = len(ohlcv_df)
    df = ohlcv_df.dropna()
    dropped_rows = initial_len - len(df)
    
    if len(df) < 34:
        raise ValueError("Insufficient data for backtesting. Minimum 34 trading days required.")
        
    WARMUP = 33  # 26 (slow EMA) + 9 (signal line) + buffer

    signals = []
    equity = 100.0
    equity_values = [100.0]
    hits = 0
    misses = 0
    neutral_days = 0

    for i in range(WARMUP, len(df) - 1):
        slice_close = df["close"].iloc[:i+1]

        rsi = calculate_rsi(slice_close)
        macd_line, signal_line, _ = calculate_macd(slice_close)
        score = composite_score(rsi, macd_line, signal_line)

        signal = score["direction"]
        close_t = df["close"].iloc[i]
        close_t1 = df["close"].iloc[i + 1]

        if signal == "Bullish":
            if close_t1 > close_t:
                result = "Hit"
                hits += 1
            else:
                result = "Miss"
                misses += 1
            equity *= float(Decimal(str(close_t1)) / Decimal(str(close_t)))
        elif signal == "Bearish":
            if close_t1 < close_t:
                result = "Hit"
                hits += 1
            else:
                result = "Miss"
                misses += 1
            equity *= float(Decimal('2') - Decimal(str(close_t1)) / Decimal(str(close_t)))
        else:
            result = "Neutral"
            neutral_days += 1

        equity_values.append(round(equity, 4))
        signals.append({
            "date": df.index[i],
            "signal": signal,
            "hit_miss": result,
            "close_T": round(close_t, 4),
            "close_T1": round(close_t1, 4),
            "equity_after": round(equity, 4)
        })

    signal_log_df = pd.DataFrame(signals)

    total_signals = hits + misses
    if total_signals == 0:
        accuracy_pct = None
    else:
        accuracy_pct = round((hits / total_signals) * 100, 1)

    return {
        "accuracy_pct": accuracy_pct,
        "total_signals": total_signals,
        "hits": hits,
        "misses": misses,
        "neutral_days": neutral_days,
        "excluded_warmup_days": WARMUP,
        "equity_curve": pd.Series(equity_values, index=df.index[WARMUP-1:len(df)-1]) if len(equity_values) > 1 else pd.Series(),
        "signal_log": signal_log_df,
        "final_equity": equity_values[-1],
        "ticker": ticker,
        "period_days": len(df)
    }
