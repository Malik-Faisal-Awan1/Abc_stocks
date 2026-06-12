import os
import pytest
from src.data_fetcher import fetch_ohlcv, fetch_sentiment

@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "true",
    reason="Requires real API key. Set RUN_INTEGRATION=true to run. Costs 2 API calls."
)
def test_full_session_live_aapl():
    """
    Fetches live OHLCV + sentiment for AAPL.
    API cost: 2 calls (1 OHLCV + 1 sentiment).
    Requires: FINNHUB_API_KEY in environment.
    """
    ohlcv = fetch_ohlcv("AAPL")
    assert not ohlcv.empty
    assert "close" in ohlcv.columns
    
    sentiment = fetch_sentiment("AAPL")
    assert "sentiment" in sentiment
    assert "news" in sentiment
