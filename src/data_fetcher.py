import json
import requests
from pathlib import Path
from typing import Union
import pandas as pd
from datetime import datetime, timedelta
import config

class ThrottleError(Exception):

class DataFetchError(Exception):

def fetch_ohlcv(ticker: str) -> pd.DataFrame:
    if config.USE_MOCK:
        return _load_mock_ohlcv(ticker)
    return _fetch_live_ohlcv(ticker)

def fetch_sentiment(ticker: str) -> dict:
    if config.USE_MOCK:
        # ASSUMPTION: Mock sentiment fetcher returns an empty list for company news since no mock file was provided for it.
        # This allows parse_sentiment to not break on empty news.
        sentiment_resp = _load_mock_sentiment()
        return {"sentiment": sentiment_resp, "news": []}
    return _fetch_live_sentiment(ticker)

def _load_mock_ohlcv(ticker: str = None) -> pd.DataFrame:
    base_path = Path(__file__).parent.parent / "data" / "mock"
    
    # Try ticker-specific file first
    if ticker:
        ticker_path = base_path / f"mock_ohlcv_{ticker.upper()}.json"
        if ticker_path.exists():
            with open(ticker_path) as f:
                return _parse_ohlcv_response(json.load(f))
                
    # Fallback to default
    path = base_path / "mock_ohlcv.json"
    with open(path) as f:
        data = json.load(f)
    return _parse_ohlcv_response(data)

def _load_mock_sentiment() -> dict:
    path = Path(__file__).parent.parent / "data" / "mock" / "mock_sentiment.json"
    with open(path) as f:
        data = json.load(f)
    return data

def _parse_ohlcv_response(data: dict) -> pd.DataFrame:
    if data.get("s") != "ok":
        raise DataFetchError(f"OHLCV response status: {data.get('s', 'unknown')}")
    return pd.DataFrame({
        "date": pd.to_datetime(data["t"], unit="s"),
        "open": data["o"],
        "high": data["h"],
        "low": data["l"],
        "close": data["c"],
        "volume": data["v"]
    }).set_index("date").sort_index()

def _call_finnhub_endpoint(path: str, params: dict) -> Union[dict, list]:
    """
    DRY helper for all Finnhub calls.
    Handles raise_for_status and JSON parsing in one place.
    """
    params["token"] = config.get_api_key()
    try:
        response = requests.get(
            f"{config.API_BASE_URL}{path}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            raise ThrottleError("Finnhub per-minute limit hit.")
        raise DataFetchError(f"HTTP Error: {str(e)}")
    except requests.exceptions.Timeout:
        raise DataFetchError("Request to Finnhub timed out.")
    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Request Error: {str(e)}")
        
    data = response.json()
    if data is None:
        raise DataFetchError(f"Finnhub returned null response for {path}")
    return data

def _fetch_live_ohlcv(ticker: str) -> pd.DataFrame:
    to_ts = int(datetime.now().timestamp())
    from_ts = int((datetime.now() - timedelta(days=120)).timestamp())

    data = _call_finnhub_endpoint("/stock/candle", {
        "symbol": ticker.upper(),
        "resolution": "D",
        "from": from_ts,
        "to": to_ts
    })

    if data.get("s") != "ok":
        raise DataFetchError(
            f"No data returned for '{ticker}'. "
            f"Finnhub status: '{data.get('s', 'unknown')}'. "
            "Verify the ticker symbol is correct."
        )

    return _parse_ohlcv_response(data)

def _fetch_live_sentiment(ticker: str) -> dict:
    
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Endpoint 1: /news-sentiment
    sentiment_data = _call_finnhub_endpoint(
        "/news-sentiment",
        {"symbol": ticker.upper()}
    )
        
    # Endpoint 2: /company-news
    news_data = _call_finnhub_endpoint(
        "/company-news",
        {"symbol": ticker.upper(), "from": from_date, "to": to_date}
    )

    return {
        "sentiment": sentiment_data,
        "news": news_data
    }
