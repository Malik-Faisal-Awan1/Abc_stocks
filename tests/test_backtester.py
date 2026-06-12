from src.backtester import run_backtest
import pandas as pd
import pytest
from unittest.mock import patch

def _make_mock_df(size=40):
    dates = pd.date_range("2026-01-01", periods=size)
    return pd.DataFrame({
        "open": range(size),
        "high": range(size),
        "low": range(size),
        "close": range(size),
        "volume": range(size)
    }, index=dates)

@patch("src.backtester.composite_score")
def test_backtest_hit_bullish(mock_score):
    df = _make_mock_df(36)
    df.loc[df.index[33], "close"] = 100
    df.loc[df.index[34], "close"] = 110 # price rises
    df.loc[df.index[35], "close"] = 120
    mock_score.return_value = {"direction": "Bullish"}
    res = run_backtest(df, "AAPL")
    assert res["hits"] > 0

@patch("src.backtester.composite_score")
def test_backtest_miss_bullish(mock_score):
    df = _make_mock_df(36)
    df.loc[df.index[33], "close"] = 100
    df.loc[df.index[34], "close"] = 90 # price falls
    df.loc[df.index[35], "close"] = 80
    mock_score.return_value = {"direction": "Bullish"}
    res = run_backtest(df, "AAPL")
    assert res["misses"] > 0

@patch("src.backtester.composite_score")
def test_backtest_hit_bearish(mock_score):
    df = _make_mock_df(36)
    df.loc[df.index[33], "close"] = 100
    df.loc[df.index[34], "close"] = 90 # price falls
    df.loc[df.index[35], "close"] = 80
    mock_score.return_value = {"direction": "Bearish"}
    res = run_backtest(df, "AAPL")
    assert res["hits"] > 0

@patch("src.backtester.composite_score")
def test_backtest_neutral_excluded(mock_score):
    df = _make_mock_df(36)
    mock_score.return_value = {"direction": "Neutral"}
    res = run_backtest(df, "AAPL")
    assert res["neutral_days"] > 0
    assert res["total_signals"] == 0
    assert res["accuracy_pct"] is None

def test_backtest_warmup_excluded():
    df = _make_mock_df(36)
    res = run_backtest(df, "AAPL")
    assert res["excluded_warmup_days"] == 33
    assert len(res["signal_log"]) == len(df) - 33 - 1

def test_backtest_insufficient_data():
    df = _make_mock_df(30)
    with pytest.raises(ValueError, match="Insufficient data"):
        run_backtest(df, "AAPL")

@patch("src.backtester.composite_score")
def test_backtest_all_neutral(mock_score):
    df = _make_mock_df(36)
    mock_score.return_value = {"direction": "Neutral"}
    res = run_backtest(df, "AAPL")
    assert res["accuracy_pct"] is None
    assert res["total_signals"] == 0

def test_backtest_equity_curve_starts_at_100():
    df = _make_mock_df(36)
    res = run_backtest(df, "AAPL")
    assert res["equity_curve"].iloc[0] == 100.0

@patch("src.backtester.composite_score")
def test_backtest_equity_compounding(mock_score):
    df = _make_mock_df(36)
    # Day 33 close = 100, Day 34 close = 110 (+10%), Day 35 close = 121 (+10%)
    df.loc[df.index[33], "close"] = 100.0
    df.loc[df.index[34], "close"] = 110.0
    df.loc[df.index[35], "close"] = 121.0
    mock_score.return_value = {"direction": "Bullish"}
    res = run_backtest(df, "AAPL")
    assert round(res["final_equity"], 2) == 121.0

def test_backtest_output_keys():
    df = _make_mock_df(40)
    res = run_backtest(df, "AAPL")
    required_keys = {
        "accuracy_pct", "total_signals", "hits", "misses",
        "neutral_days", "excluded_warmup_days", "equity_curve",
        "signal_log", "final_equity", "ticker", "period_days"
    }
    assert set(res.keys()) == required_keys

def test_backtest_signal_log_columns():
    df = _make_mock_df(40)
    res = run_backtest(df, "AAPL")
    assert list(res["signal_log"].columns) == ["date", "signal", "hit_miss", "close_T", "close_T1", "equity_after"]
