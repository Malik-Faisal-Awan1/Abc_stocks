import pytest
from src.sentiment import parse_sentiment

def test_parse_sentiment_bullish():
    sentiment_resp = {
        "sentiment": {"bullishPercent": 0.7, "bearishPercent": 0.3},
        "companyNewsScore": 0.8
    }
    parsed = parse_sentiment(sentiment_resp, [])
    assert parsed["is_valid"] is True
    assert parsed["label"] == "Bullish"

def test_parse_sentiment_bearish():
    sentiment_resp = {
        "sentiment": {"bullishPercent": 0.3, "bearishPercent": 0.7},
        "companyNewsScore": 0.4
    }
    parsed = parse_sentiment(sentiment_resp, [])
    assert parsed["is_valid"] is True
    assert parsed["label"] == "Bearish"

def test_parse_sentiment_missing_data():
    parsed = parse_sentiment({}, [])
    assert parsed["is_valid"] is False
    assert "reason" in parsed

def test_attribution_always_present():
    sentiment_resp = {
        "sentiment": {"bullishPercent": 0.7, "bearishPercent": 0.3},
        "companyNewsScore": 0.8
    }
    parsed = parse_sentiment(sentiment_resp, [])
    assert "attribution" in parsed
    assert "Finnhub" in parsed["attribution"]
